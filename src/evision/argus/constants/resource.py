#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-11-29 13:48
# @version: 1.0
#
from enum import IntEnum


class DeviceType(IntEnum):
    # 图像源
    IMAGE_SOURCE = 1
    # 终端、面板机
    TERMINAL = 2
    # 服务器
    SERVER = 3


class ImageSourceType(IntEnum):
    """ Identify image source type
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
