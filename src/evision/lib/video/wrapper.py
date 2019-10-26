#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-25 16:24
# @version: 1.0
#
from evision.lib.log import logutil

from evision.lib.entity import Zone, ImageFrame
from evision.lib.video import BaseImageSource, ImageSourceUtil

logger = logutil.get_logger()

__all__ = [
    'ImageSourceWrapperConfig',
    'ImageSourceWrapper'
]


class ImageSourceWrapperConfig(object):
    """ Wrapper configuration of image source
    """
    width: int
    height: int
    zone: [Zone, None]

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
            self.zone = Zone(zone_start_x, zone_start_y, zone_width, zone_height)

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
    _image_source: BaseImageSource

    width: [int, None]
    height: [int, None]
    zone: [Zone, None]

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
                                   self._image_source.random_frame_id(),
                                   frame, self.zoom_ratio, self.zone)
                        for frame in frames]
        return image_frames[0] if n_frame == 1 else image_frames

    def is_alive(self):
        return self._image_source.is_alive()
