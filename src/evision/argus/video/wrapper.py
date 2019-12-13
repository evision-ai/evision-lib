#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-25 16:24
# @version: 1.0
#
import time
from typing import Union, Set

import numpy as np
from walrus import Database

from evision.argus.video import BaseImageSource, ImageSourceUtil
from evision.argus.video.schema import ImageSourceReaderConfig
from evision.lib.entity import ImageFrame, Zone
from evision.lib.log import logutil
from evision.lib.util import CacheUtil
from evision.lib.util.redis import RedisNdArrayQueueReader, RedisQueue

logger = logutil.get_logger()

__all__ = [
    'ImageSourceWrapperConfig',
    'ImageSourceWrapper',
    'ImageSourceReader'
]

FrameDataType = str

class ImageSourceReader(object):
    width: Union[int, None]
    height: Union[int, None]
    zone: Union[Zone, None]
    _frame_queue: RedisQueue
    _db: Database()
    _last_frames: Set[FrameDataType]

    def __init__(self, config: ImageSourceReaderConfig):
        self.source_id = config.source_id
        self._frame_queue = RedisQueue(ImageSourceUtil.frames_key(config.source_id))
        self.source_width, self.source_height = config.frame_size.to_tuple()
        self.width, self.height = None, None
        if config.zoom_size is not None:
            self.width, self.height = config.zoom_size.to_tuple()
        self.zone = config.zone
        self.process_rate = config.process_rate if config.process_rate else config.fps
        self._frame_interval = float(1) / self.process_rate
        self.name = config.name if config.name else CacheUtil.random_id()
        self._last_frames = set()

    @property
    def zoom_ratio(self):
        """更新视频源图像帧的缩放比"""
        if self.width and self.source_width:
            return float(self.width) / self.source_width
        if self.height and self.source_height:
            return float(self.height) / self.source_height
        return 1.0

    @zoom_ratio.setter
    def zoom_ratio(self, zoom_ratio):
        self.width = zoom_ratio * self.source_width
        self.height = zoom_ratio * self.source_height

    def provide(self, n_frame=1, block=True, timeout=1, deduplicate = True
            ) -> Union[FrameDataType, List[FrameDataType], None]:
        frames: List[FrameDataType] = None
        if not block:
            frames = self._frame_queue.get(n_frame)
            if (not frames) or deduplicate and set.intersection(frames):
                return None
        else:
            start = time.time()
            must_large_than, must_end = start - 0.05, start + timeout
            while must_large_than <= time.time() < must_end:
                queue_size, frames = self._frame_queue.lrange(n_frame)
                frames = [
                    frame for frame in frames
                    if not (deduplicate and frame in self._last_frames)
                ] if frames is not None else []
                if len(frames) < n_frame:
                    # query for 10 times every second
                    time.sleep(min(0.1, self._frame_interval / 3) * (n_frame - queue_size))
            if len(frames) < n_frame:
                return None

        image_frames = [
            ImageFrame(self.source_id,
                       frame,
                       None, self.zoom_ratio, self.zone)
            for frame in frames
        ]
        if deduplicate:
            self._last_frames = set(frames)
        return image_frames[0] if n_frame == 1 else image_frames


class ImageSourceWrapperConfig(object):
    """ #deprecated Wrapper configuration of image source
    """
    width: int
    height: int
    zone: Union[Zone, None]

    def __init__(self, width: int, height: int,
                 zone_start_x: int = 0, zone_start_y: int = 0,
                 zone_width: int = None, zone_height: int = None):
        """图像源数据封装，目前支持对图像进行缩放和裁剪
        NOTE: 先缩放，后裁剪

        :param width: 缩放后图像源宽度
        :param height: 缩放后图像源高度
        :param zone_start_x:裁剪区域起始点横坐标
        :param zone_start_y:裁剪区域起始点纵坐标
        :param zone_width:裁剪区域宽度
        :param zone_height:裁剪区域高度
        """
        self.width = width
        self.height = height

        if not zone_width or not zone_height:
            self.zone = None
        else:
            self.zone = Zone(start_x=zone_start_x, start_y=zone_start_y,
                             width=zone_width, height=zone_height)

        self.validate()

    @property
    def size(self):
        """图像源缩放尺寸"""
        if not self.width or not self.height:
            return None
        return self.width, self.height

    @size.setter
    def size(self, size):
        assert size and hasattr(size, '__iter__') and len(size) == 2
        width, height = size
        if width == self.width and height == self.height:
            return
        self.width, self.height = ImageSourceUtil.check_frame_shape(width, height)

    def validate(self, frame_width: int = None, frame_height: int = None):
        """ 校验视频源处理配置

        :param frame_width: 图像源原始宽度
        :param frame_height:  图像源原始高度
        """
        if frame_width is None or frame_height is None:
            return
        self._validate_zoom()
        self._validate_zone(frame_width, frame_height)

    def _validate_zoom(self):
        """ 校验视频源缩放配置
        """
        if self.width is None and self.height is None:
            return
        ImageSourceUtil.check_frame_shape(self.width, self.height)

    def _validate_zone(self, frame_width: int = None, frame_height: int = None):
        """ 校验视频源区域配置

        :param frame_width: 图像源原始宽度
        :param frame_height:  图像源原始高度
        """
        if not self.zone:
            return
        if self.width and self.height:
            self.zone.validate_shape(self.width, self.height)
        elif frame_width and frame_height:
            self.zone.validate_shape(frame_width, frame_height)

    def __getattr__(self, item):
        return getattr(self.zone, item)


class ImageSourceWrapper(object):
    """#deprecated"""
    _image_source: BaseImageSource

    width: Union[int, None]
    height: Union[int, None]
    zone: Union[Zone, None]

    def __init__(self, image_source: BaseImageSource,
                 wrapper_config: ImageSourceWrapperConfig = None):
        """

        :param image_source: 图像源配置
        :param wrapper_config: 图像源封装配置
        """
        assert image_source
        self._image_source = image_source

        self.zone = None
        self.width, self.height = image_source.width, image_source.height
        if wrapper_config:
            self.__dict__.update(wrapper_config.__dict__)

    @property
    def name(self):
        return self._image_source.alias

    @property
    def zoom_ratio(self):
        """更新视频源图像帧的缩放比"""
        if self.width and self._image_source.width:
            return float(self.width) / self._image_source.width
        if self.height and self._image_source.height:
            return float(self.height) / self._image_source.height
        return 1.0

    @zoom_ratio.setter
    def zoom_ratio(self, zoom_ratio):
        self.width = zoom_ratio * self._image_source.width
        self.height = zoom_ratio * self._image_source.height

    def provide(self, n_frame=1, block=True, timeout=1):
        frames = self._image_source.current(n_frame, block, timeout)
        if not frames:
            return None
        image_frames = [ImageFrame(self._image_source.source_id,
                                   ImageSourceUtil.random_frame_id(self._image_source.source_id),
                                   frame, self.zoom_ratio, self.zone)
                        for frame in frames]
        return image_frames[0] if n_frame == 1 else image_frames

    def is_alive(self):
        return self._image_source.running

    @property
    def source_id(self):
        return self._image_source.source_id

    @property
    def uri_and_type(self):
        return self._image_source.uri_and_type

    def open_image_source(self):
        if not self._image_source:
            raise ValueError('No image source configured')
        if self.is_alive():
            logger.debug('Image source={} already started', self.source_id)
            return

        with self._image_source.read_lock:
            if not self._image_source.running:
                self._image_source.setDaemon(True)
                self._image_source.start()
                time.sleep(1)
