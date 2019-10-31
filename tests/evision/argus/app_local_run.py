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

from evision.argus.app import ArgusApplicationConfig, DummyApplication
from evision.lib.log import logutil
from evision.lib.video import ImageSourceType, ImageSourceWrapperConfig
from evision.lib.video.source import VideoFileImageSource

logger = logutil.get_logger()
# logger.setLevel(logging.DEBUG)

__local_video__ = os.path.expanduser('~/Downloads/test.avi')

__wrapper_config__ = ImageSourceWrapperConfig(
    width=960, height=540,
    zone_start_x=80, zone_start_y=70, zone_width=800, zone_height=400)

source = VideoFileImageSource(
    endless=True,
    source_uri=__local_video__, source_type=ImageSourceType.VIDEO_FILE)


def test_app_config():
    app_config = ArgusApplicationConfig(
        source_wrapper_config=__wrapper_config__,
        fps=1,
        name='test-dummy-app'
    )
    app = DummyApplication.construct(app_config, source=source)
    app.run()


def test_multiple_apps():
    logger.info('Source status: {}', source.is_alive())
    app_config1 = ArgusApplicationConfig(
        source_wrapper_config=__wrapper_config__,
        fps=1,
        name='test-app1'
    )
    app_config2 = ArgusApplicationConfig(
        source_wrapper_config=__wrapper_config__,
        fps=2,
        name='test-app2'
    )
    app1 = DummyApplication.construct(app_config1, source=source)
    app2 = DummyApplication.construct(app_config2, source=source)
    logger.debug('Source status: {}', source.is_alive())
    logger.debug('App status, app1={}, app2={}', app1.is_inited(), app2.is_inited())
    logger.debug('App status, app1={}, app2={}', app1._inited, app2._inited)
    app1.start()
    app2.start()
    time.sleep(3)
    app1.stop()
    app2.stop()
    logger.info('Source status: {}', source.is_alive())
    source.stop()
    time.sleep(1)
    logger.info('Source status: {}', source.is_alive())


if __name__ == '__main__':
    # test_app_config()
    test_multiple_apps()
