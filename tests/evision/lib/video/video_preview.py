# -*- coding: utf-8 -*-
#
# Copyright 2018 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-07-21 15:54
# @version: 1.0
#

from evision.lib.video import (
    ImageSourceType, VideoCaptureSource,
    ImageSourceWrapper, ImageSourceWrapperConfig,
    ImageSourcePreview
)
from evision.lib.video.source import VideoFileImageSource

width, height = 960, 540


def _open_image_source(source):
    wrapper_config = ImageSourceWrapperConfig(
        width=width, height=height,
        zone_start_x=80, zone_start_y=70, zone_width=800, zone_height=400)
    wrapper = ImageSourceWrapper(source, wrapper_config)

    source.daemon = True
    source.start()
    preview = ImageSourcePreview(wrapper)
    preview.run()
    source.stop()


def with_ip_camera():
    source_config = 'rtsp://admin:password@192.100.1.134:554/h264/ch1/main/av_stream'
    source_type = ImageSourceType.IP_CAMERA
    source = VideoCaptureSource(source=source_config, source_type=source_type)
    _open_image_source(source)


def with_usb_camera():
    source_config = 0
    source_type = ImageSourceType.USB_CAMERA
    source = VideoCaptureSource(source=source_config, source_type=source_type,
                                width=width, height=height)
    _open_image_source(source)


def with_video_file():
    import os
    source_config = os.path.expanduser('~/Downloads/test.avi')
    source_type = ImageSourceType.VIDEO_FILE
    source = VideoFileImageSource(source_config, source_type)
    _open_image_source(source)


if __name__ == '__main__':
    with_video_file()