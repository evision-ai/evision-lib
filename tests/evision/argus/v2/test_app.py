# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-11-01 18:58
# @version: 1.0
#
from evision.argus.constants.task import TaskType
from evision.argus.v2.app import BaseArgusApp, DummyApp


def test_app_names():
    assert BaseArgusApp.get_handler_by_name('DUMMY') == DummyApp
    assert BaseArgusApp.get_handler_by_name(TaskType.DUMMY) == DummyApp
