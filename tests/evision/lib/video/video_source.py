#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-11-25 09:45
# @version: 1.0
#

from evision.lib.video import ImageSourceType, VideoCaptureSource, VideoFileImageSource

width, height = 960, 540


def with_usb_camera():
    source_uri = 0
    source_type = ImageSourceType.USB_CAMERA
    source = VideoCaptureSource(source_uri=source_uri, source_type=source_type,
                                width=width, height=height)

    source.run()


def with_video_file():
    import os
    source_uri = os.path.expanduser('~/Downloads/test.avi')
    source_type = ImageSourceType.VIDEO_FILE
    source = VideoFileImageSource(source_uri=source_uri, source_type=source_type)
    source.run()


if __name__ == '__main__':
    with_usb_camera()
    # with_video_file()
    pass
