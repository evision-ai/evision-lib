#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-18 10:29
# @version: 1.0
import time

from evision.lib.log import logutil
from evision.lib.util.types import ValueAsStrIntEnum

logger = logutil.get_logger()

__all__ = [
    'ImageSourceType',
    'ImageSourceUtil'
]


class ImageSourceType(ValueAsStrIntEnum):
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


class ImageSourceUtil(object):
    DEFAULT_TYPE = ImageSourceType.IP_CAMERA

    @classmethod
    def parse_source_config(cls, source_, type_):
        """根据来源和来源类型获取图像源信息"""
        # video source setting
        type_ = cls.DEFAULT_TYPE if type_ is None else ImageSourceType(type_)

        if ImageSourceType.USB_CAMERA == type_ and not isinstance(source_, int):
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

    @staticmethod
    def random_frame_id(source_id):
        """ 生成随机图像帧ID"""
        return '{}-{:d}'.format(source_id, int(1000 * time.time()))
