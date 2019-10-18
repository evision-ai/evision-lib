#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-18 10:29
# @version: 1.0
#
from enum import Enum

from evision.lib.log import logutil

logger = logutil.get_logger()

__all__ = [
    'ImageSourceType',
    'ImageSourceUtil'
]


class ImageSourceType(Enum):
    """ Identify video source type
    """
    # 网络摄像头
    IP_CAMERA = 1
    # USB 摄像头
    USB_CAMERA = 2
    # 视频文件
    VIDEO_FILE = 3
    # 视频链接
    VIDEO_LINK = 4
    # 图片链接
    IMAGE_LINK = 5
    # 图片文件
    IMAGE_FILE = 6

    def equals(self, value):
        if value is None:
            return False
        elif isinstance(value, int):
            return self.value == value
        elif isinstance(value, ImageSourceType):
            return self.value == value.value
        else:
            return False


class ImageSourceUtil(object):
    DEFAULT_TYPE = ImageSourceType.IP_CAMERA

    @classmethod
    def parse_source_config(cls, source_, type_):
        """根据来源和来源类型获取图像源信息"""
        # video source setting
        if type_ is None:
            type_ = cls.DEFAULT_TYPE
        elif isinstance(type_, int):
            type_ = ImageSourceType(type_)
        elif not isinstance(type_, ImageSourceType):
            raise ValueError('Invalid video source type={}'.format(type_))

        if ImageSourceType.USB_CAMERA.equals(type_) and not isinstance(source_, int):
            source_ = int(source_)

        logger.info('Video source=[{}], type=[{}]', source_, type_)
        return source_, type_

    @staticmethod
    def check_frame_shape(width, height):
        if not width and not height:
            raise ValueError('Frame shape not provided')
        if not width or not height:
            raise ValueError('Frame width and height should be both or either '
                             'set, provided=[{}, {}]', width, height)
        if width < 1 or height < 1:
            raise ValueError('Invalid camera frame size=[{}, {}]'.format(width, height))
        return width, height
