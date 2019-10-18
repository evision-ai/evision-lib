# -*- coding: utf-8 -*-
#
# Copyright 2018 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-07-21 15:54
# @version: 1.0
#
import pytest

from evision.lib.video.base import ImageSourceType
from evision.lib.video import VideoCapturePreview, VideoCaptureZoomedSource

width, height = 960, 540


def start_camera(video_source):
    video_source.daemon = True
    video_source.start()

    preview = VideoCapturePreview(video_source)
    preview.run()

    video_source.stop_reading()


@pytest.skip
def test_ip_camera():
    _source = 'rtsp://admin:password@192.100.1.134:554/h264/ch1/main/av_stream'
    video_source = VideoCaptureZoomedSource(_source, ImageSourceType.IP_CAMERA,
                                            width, height, 5)
    start_camera(video_source)


@pytest.skip
def test_usb_camera():
    video_source = VideoCaptureZoomedSource(0, ImageSourceType.USB_CAMERA,
                                            width, height, 5)
    start_camera(video_source)


@pytest.skip
def test_video_file():
    import os
    video_file = os.path.expanduser('~/Downloads/test.avi')
    video_source = VideoCaptureZoomedSource(video_file, ImageSourceType.VIDEO_FILE,
                                            width, height, 5)
    start_camera(video_source)


if __name__ == '__main__':
    test_video_file()
