#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-31 14:24
# @version: 1.0
#
import logging
import os
import time

from evision.argus.app import App, ArgusApplicationConfig
from evision.argus.constants.resource import ImageSourceType
from evision.argus.coordinator import ArgusCoordinator, DictImageSourceCoordinator
from evision.argus.video import ImageSourceConfig, ImageSourcePreview, ImageSourceWrapperConfig
from evision.argus.video import VideoCaptureSource, VideoFileImageSource
from evision.lib.log import logutil

logger = logutil.get_logger()
logger.setLevel(logging.DEBUG)

__wrapper_config__ = ImageSourceWrapperConfig(
    width=960, height=540,
    zone_start_x=80, zone_start_y=70, zone_width=800, zone_height=400)

__local_video__ = os.path.expanduser('~/Downloads/test.avi')
image_source_config = ImageSourceConfig(
    source_uri=__local_video__, source_type=ImageSourceType.VIDEO_FILE,
    handler_name='VIDEO_FILE', endless=True)

__ip_camera__ = 'rtsp://admin:1111aaaa@192.100.1.189:554/h264/ch1/main/av_stream'
ip_camera_config = ImageSourceConfig(
    # source_uri=__ip_camera__, source_type=ImageSourceType.IP_CAMERA,
    source_uri=0, source_type=ImageSourceType.USB_CAMERA,
    handler_name='VIDEO_CAPTURE'
)

source_coordinator = DictImageSourceCoordinator()
coordinator = ArgusCoordinator()


def test_source_registering():
    source = source_coordinator.register(image_source_config)
    assert isinstance(source, VideoFileImageSource)
    assert source.endless


def test_ip_camera_registering():
    source1 = source_coordinator.register(ip_camera_config)
    assert isinstance(source1, VideoCaptureSource)
    source2 = source_coordinator.register(ip_camera_config, VideoFileImageSource)
    assert isinstance(source2, VideoCaptureSource)
    assert source1 is source2
    source1.daemon = True
    source1.start()
    preview = ImageSourcePreview(source1)
    preview.run()

    source1.stop()


def test_coordinator():
    app_config1 = ArgusApplicationConfig(
        image_source_config=image_source_config,
        source_wrapper_config=__wrapper_config__,
        fps=0.5,
        name='test-app1', app_handler=App.dummy)
    app_config2 = ArgusApplicationConfig(
        image_source_config=image_source_config,
        source_wrapper_config=__wrapper_config__,
        fps=0.2,
        name='test-app2', app_handler=App.dummy)
    app_config3 = ArgusApplicationConfig(
        image_source_config=ip_camera_config,
        source_wrapper_config=__wrapper_config__,
        fps=0.5,
        name='test-app3', app_handler=App.dummy)
    coordinator.add(app_config1)
    coordinator.add(app_config2)
    coordinator.add(app_config3)
    assert 2 == coordinator.n_image_sources
    assert 3 == coordinator.n_apps
    coordinator.run()
    time.sleep(10)
    coordinator.stop()


if __name__ == '__main__':
    # test_ip_camera_registering()
    test_coordinator()
    pass
