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


class VideoSourceType(Enum):
    """ Identify video source type
    """
    IP_CAMERA = 1
    USB_CAMERA = 2
    VIDEO_FILE = 3

    def equals(self, value):
        if value is None:
            return False
        elif isinstance(value, int):
            return self.value == value
        elif isinstance(value, VideoSourceType):
            return self.value == value.value
        else:
            return False
