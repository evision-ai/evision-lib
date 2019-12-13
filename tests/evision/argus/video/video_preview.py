# -*- coding: utf-8 -*-
#
# Copyright 2018 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-07-21 15:54
# @version: 1.0
#
import logging
import time

from evision.argus.constants.resource import ImageSourceHandler, ImageSourceType
from evision.argus.video import BaseImageSource
from evision.argus.video import ImageSourceConfig, ImageSourcePreview
from evision.argus.video import ImageSourceReader
from evision.argus.video import ImageSourceReaderConfig
from evision.lib.entity import Shape
from evision.lib.log import logutil

width, height = 480, 270

logger = logutil.get_logger()
logger.setLevel(logging.DEBUG)


def _open_image_source(source_config: ImageSourceConfig):
    source_config.frame_size = Shape(width=width, height=height)
    source_config.process_rate = 100
    source = BaseImageSource.construct(source_config)
    source.daemon = True
    # source.start()

    while not source.running and False:
        logger.debug('Waiting for source initializing...')
        time.sleep(0.5)

    source_config.source_id = source.source_id
    wrapper_config = ImageSourceReaderConfig(
        **source_config.dict(), zoom_size=Shape(width=width, height=height))
    wrapper = ImageSourceReader(wrapper_config)

    preview = ImageSourcePreview(wrapper)
    preview.run()
    source.stop()


def with_ip_camera():
    source_uri = 'rtsp://admin:1111aaaa@192.100.1.112:554/h264/ch1/main/av_stream'
    source_type = ImageSourceType.IP_CAMERA
    source_config = ImageSourceConfig(source_id="cam1", source_uri="cam1", source_type=source_type,
                                      handler_name=ImageSourceHandler.VIDEO_CAPTURE)
    _open_image_source(source_config)


def with_usb_camera():
    source_uri = 0
    source_type = ImageSourceType.USB_CAMERA
    source_config = ImageSourceConfig(source_uri=source_uri, source_type=source_type,
                                      handler_name=ImageSourceHandler.VIDEO_CAPTURE)
    _open_image_source(source_config)


def with_video_file():
    import os
    source_uri = os.path.expanduser('~/Downloads/test.avi')
    source_type = ImageSourceType.VIDEO_FILE
    source_config = ImageSourceConfig(source_uri=source_uri, source_type=source_type,
                                      handler_name=ImageSourceHandler.VIDEO_FILE)
    _open_image_source(source_config)


if __name__ == '__main__':
    # with_ip_camera()
    # with_usb_camera()
    with_ip_camera()
    pass
