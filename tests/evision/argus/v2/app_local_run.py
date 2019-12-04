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
from evision.argus.v2.app import BaseArgusAppConfig, DummyApp
from evision.argus.video import BaseImageSource, ImageSourceReaderConfig
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
source = BaseImageSource.construct(source_wrapper_config[_test_source_id])
source.daemon = True
source.start()


def test_app_config():
    app_config = BaseArgusAppConfig(
        frame_rate=1,
        app_name='test-dummy-app',
        source_ids={'usb'},
        group_ids={'random'},
        source_wrapper_config=source_wrapper_config,
    )
    app = DummyApp.construct(app_config)
    app.show_error = True
    app.fail_on_error = True
    app.run()


def test_multiple_apps():
    app_config1 = BaseArgusAppConfig(
        app_name='test-app1',
        source_ids={_test_source_id, },
        group_ids={'random'},
        source_wrapper_config=source_wrapper_config
    )
    app_config2 = BaseArgusAppConfig(
        app_name='test-app2',
        source_ids={_test_source_id, },
        group_ids={'random'},
        source_wrapper_config=source_wrapper_config
    )
    app1 = DummyApp.construct(app_config1)
    app2 = DummyApp.construct(app_config2)
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
