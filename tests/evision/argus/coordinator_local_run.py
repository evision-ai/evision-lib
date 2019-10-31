#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-31 14:24
# @version: 1.0
#

import os
import time

from evision.argus.app import ArgusApplicationConfig, DummyApplication
from evision.argus.coordinator import ArgusCoordinator, DictImageSourceCoordinator
from evision.lib.video import ImageSourceConfig, ImageSourceType, ImageSourceWrapperConfig
from evision.lib.video.source import VideoFileImageSource

__local_video__ = os.path.expanduser('~/Downloads/test.avi')

__wrapper_config__ = ImageSourceWrapperConfig(
    width=960, height=540,
    zone_start_x=80, zone_start_y=70, zone_width=800, zone_height=400)

image_source_config = ImageSourceConfig(
    source_uri=__local_video__, source_type=ImageSourceType.VIDEO_FILE,
    extra={
        'endless': True
    })

source_coordinator = DictImageSourceCoordinator()
coordinator = ArgusCoordinator()


def test_source_registering():
    source = source_coordinator.register(image_source_config, VideoFileImageSource)
    assert isinstance(source, VideoFileImageSource)
    assert source.endless


def test_coordinator():
    app_config1 = ArgusApplicationConfig(
        image_source_config=image_source_config,
        source_wrapper_config=__wrapper_config__,
        fps=0.5,
        name='test-app1'
    )
    app_config2 = ArgusApplicationConfig(
        image_source_config=image_source_config,
        source_wrapper_config=__wrapper_config__,
        fps=0.2,
        name='test-app2'
    )
    coordinator.add(app_config1, app_type=DummyApplication, source_type=VideoFileImageSource)
    coordinator.add(app_config2, app_type=DummyApplication, source_type=VideoFileImageSource)
    assert 1 == coordinator.n_image_sources
    assert 2 == coordinator.n_apps
    time.sleep(3)
    coordinator.stop()


if __name__ == '__main__':
    test_coordinator()
