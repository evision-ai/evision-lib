# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-11-01 18:58
# @version: 1.0
#
from evision.argus.constants.task import TaskType
from evision.argus.v2.app import BaseArgusApp, BaseArgusAppConfig, DummyApp
from evision.argus.video import ImageSourceReaderConfig


def test_app_names():
    assert BaseArgusApp.get_handler_by_name('DUMMY') == DummyApp
    assert BaseArgusApp.get_handler_by_name(TaskType.DUMMY) == DummyApp


def test_image_source_reader_config():
    config = ImageSourceReaderConfig(source_id=2, source_uri=0)
    assert config.source_id == '2'


def test_base_app_config():
    config = BaseArgusAppConfig(
        source_ids=[1, ],
        group_ids=[2, 3, 4],
        source_wrapper_config={
            '1': ImageSourceReaderConfig(source_id=1, source_uri=0),
        }
    )
    assert len(config.source_ids) == 1
    assert len(config.group_ids) == 3
