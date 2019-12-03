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

from evision.argus.constants.resource import ImageSourceHandler, ImageSourceType
from evision.argus.v2.app import BaseArgusAppConfig
from evision.argus.v2.coordinator import ArgusCoordinator, DictImageSourceCoordinator
from evision.argus.video import ImageSourcePreview, ImageSourceReaderConfig
from evision.argus.video import VideoCaptureSource, VideoFileImageSource
from evision.lib.entity import Shape, Zone
from evision.lib.log import logutil

logger = logutil.get_logger()
logger.setLevel(logging.DEBUG)

__local_video__ = os.path.expanduser('~/Downloads/test.avi')
__ip_camera__ = 'rtsp://admin:1111aaaa@192.100.1.189:554/h264/ch1/main/av_stream'

__configs = dict(
    frame_size=Shape(width=1920, height=1080),
    zone=Zone(start_x=40, start_y=35, width=400, height=200),
    zoom_size=Shape(width=480, height=270)
)
_test_source_id = 'local'
source_wrapper_config = {
    'usb': ImageSourceReaderConfig(
        source_id='usb',
        source_uri=0, source_type=ImageSourceType.USB_CAMERA,
        **__configs),
    'local': ImageSourceReaderConfig(
        source_id='local',
        source_uri=__local_video__, source_type=ImageSourceType.VIDEO_FILE,
        handler_name=ImageSourceHandler.VIDEO_FILE, endless=True,
        **__configs),
    'ip': ImageSourceReaderConfig(
        source_id='ip',
        source_uri=__ip_camera__, source_type=ImageSourceType.IP_CAMERA,
        **__configs),
}

source_coordinator = DictImageSourceCoordinator()
coordinator = ArgusCoordinator()


def test_source_registering():
    source = source_coordinator.register(source_wrapper_config['local'])
    assert isinstance(source, VideoFileImageSource)
    assert source.endless


def test_usb_camera_registering():
    source1 = source_coordinator.register(source_wrapper_config['usb'])
    assert isinstance(source1, VideoCaptureSource)
    source2 = source_coordinator.register(source_wrapper_config['usb'], VideoFileImageSource)
    assert isinstance(source2, VideoCaptureSource)
    assert source1 is source2
    preview = ImageSourcePreview(source1)
    preview.run()

    source1.stop()


def test_ip_camera_registering():
    source1 = source_coordinator.register(source_wrapper_config['ip'])
    assert isinstance(source1, VideoCaptureSource)
    source2 = source_coordinator.register(source_wrapper_config['ip'], VideoFileImageSource)
    assert isinstance(source2, VideoCaptureSource)
    assert source1 is source2
    preview = ImageSourcePreview(source1)
    preview.run()

    source1.stop()


def test_coordinator():
    app_config1 = BaseArgusAppConfig(
        app_name='test-app1', frame_rate=0.5,
        source_ids=[_test_source_id, ], group_ids=['random'],
        source_wrapper_config=source_wrapper_config)
    app_config2 = BaseArgusAppConfig(
        app_name='test-app2', frame_rate=0.2,
        source_ids=[_test_source_id, ], group_ids=['random'],
        source_wrapper_config=source_wrapper_config)
    coordinator.add(app_config1)
    coordinator.add(app_config2)
    time.sleep(0.5)
    assert 1 == coordinator.n_image_sources
    assert 2 == coordinator.n_apps, f'incorrect number of apps: {coordinator.n_apps}'
    app_config3 = BaseArgusAppConfig(
        app_name='test-app3', frame_rate=0.5,
        source_ids=['usb', ], group_ids=['random'],
        source_wrapper_config=source_wrapper_config)
    coordinator.add(app_config3)
    assert 2 == coordinator.n_image_sources
    assert 3 == coordinator.n_apps
    coordinator.run()
    time.sleep(10)
    coordinator.stop()


if __name__ == '__main__':
    # test_source_registering()
    # test_usb_camera_registering()
    # test_ip_camera_registering()
    test_coordinator()
    pass
