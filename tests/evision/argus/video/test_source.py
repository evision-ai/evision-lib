# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-11-01 16:47
# @version: 1.0
#

from evision.argus.video import *


def test_image_source_handler_names():
    assert BaseImageSource.handlers
    assert VideoCaptureSource.handlers
    assert BaseImageSource.get_handler_by_name('VIDEO_CAPTURE') == VideoCaptureSource
    assert BaseImageSource.get_handler_by_name(ImageSourceHandler.VIDEO_CAPTURE) == VideoCaptureSource
    assert BaseImageSource.get_handler_by_name('VIDEO_FILE') == VideoFileImageSource
    assert BaseImageSource.get_handler_by_name(ImageSourceHandler.VIDEO_FILE) == VideoFileImageSource
