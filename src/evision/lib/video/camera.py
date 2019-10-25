#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-12 15:56
# @version: 1.0
#

import time

import cv2
import numpy as np

from evision.lib.log import LogHandlers, logutil
from evision.lib.video import BaseImageSource, ImageSourceType, ImageSourceUtil

logger = logutil.get_logger(LogHandlers.DEFAULT)


class VideoCaptureImageSource(BaseImageSource):
    """VideoCapture类型的视频源封装
    支持视频源类型：
    - 网络摄像头：ImageSourceType.IP_CAMERA
    - USB 摄像头：ImageSourceType.USB_CAMERA
    - 本地视频文件：ImageSourceType.VIDEO_FILE
    """
    source: cv2.VideoCapture

    def read_frame(self):
        """从视频源直接获取图像帧"""
        with self._lock:
            ret, camera_frame = self.source.read()
            if not ret or np.all(camera_frame == 0):
                self.accumulate_failure_count()
                self.try_restore(self._MAX_FAIL_TIMES, self.reload_source)
                time.sleep(self.frame_interval)
                return None
            self.reset_failure_count()
            return camera_frame

    @staticmethod
    def validate_source(source_config, source_type, release=True):
        source_config, source_type = ImageSourceUtil.parse_source_config(
            source_config, source_type)
        """验证VideoCapture对象是否有效"""
        source_ = cv2.VideoCapture(source_config)
        if not source_.isOpened():
            logger.warning('Failed connecting to camera=[{}], type={}',
                           source_config, source_type)
            return None

        ret, frame = source_.read()

        if not ret:
            logger.warning('Camera[{}, type={}] opened but failed getting frame',
                           source_config, source_type)
            return None

        if release:
            source_.release()
            return frame

        return source_

    def on_start(self):
        """创建VideoCapture对象"""
        source_ = self.validate_source(self.source_config, self.source_type,
                                       release=False)
        if source_ is None or not source_.isOpened():
            raise Exception('无法连接到摄像头/视频源，请检查')

        self.source = source_
        self.frame_size = self.source.get(cv2.CAP_PROP_FRAME_WIDTH), \
                          self.source.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = self.source.get(cv2.CAP_PROP_FPS)
        logger.info('连接到视频源[{}], type={}，size=({}), fps={}',
                    self.source_config, self.source_type,
                    self.frame_size, self.fps)

    def reload_source(self):
        """重新连接视频源

        USB 摄像头不允许并行连接，必须先释放现有连接
        """
        self.reset_failure_count()
        with self._lock:
            if self.source.isOpened() \
                and ImageSourceType.USB_CAMERA == self.source_type:
                self.source.release()
            source_ = self.validate_source(
                self.source_config, self.source_type, release=False)
            if source_ is None or not source_.isOpened():
                raise Exception('Failed initialized video source={}'.format(
                    self.source))
            if self.source.isOpened():
                self.source.release()
            self.source = source_
        logger.info('Reload video source={}', self.source)

    def on_stop(self):
        if self.source and self.source.isOpened():
            self.source.release()
            del self.source
