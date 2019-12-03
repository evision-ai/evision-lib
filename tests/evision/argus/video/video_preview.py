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

from evision.lib.entity import Shape
from evision.lib.log import logutil
from evision.argus.video import ImageSourcePreview, ImageSourceType, ImageSourceConfig
from evision.argus.video import BaseImageSource
from evision.argus.constants.resource import ImageSourceHandler
from evision.argus.video import ImageSourceReader
from evision.argus.video.schema import ImageSourceReaderConfig

width, height = 960, 540

logger = logutil.get_logger()
logger.setLevel(logging.DEBUG)


def _open_image_source(source_config: ImageSourceConfig):
    source = BaseImageSource.construct(source_config)
    source.daemon = True
    source.start()

    while not source.running:
        logger.debug('Waiting for source initializing...')
        time.sleep(0.5)

    source_config.source_id = source.source_id
    source_config.frame_size = Shape.parse(source.frame_size)
    wrapper_config = ImageSourceReaderConfig(
        **source_config.dict(), zoom=Shape(width=960, height=540))
    wrapper = ImageSourceReader(wrapper_config)

    preview = ImageSourcePreview(wrapper)
    preview.run()
    source.stop()


def with_ip_camera():
    source_uri = 'rtsp://admin:1111aaaa@192.100.1.112:554/h264/ch1/main/av_stream'
    source_type = ImageSourceType.IP_CAMERA
    source_config = ImageSourceConfig(source_uri=source_uri, source_type=source_type,
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
    with_video_file()
    pass
