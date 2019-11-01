# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-11-01 18:58
# @version: 1.0
#
from evision.argus.app import App, ArgusApp, DummyApplication


def test_app_names():
    assert ArgusApp.get_handler_by_name('dummy') == DummyApplication
    assert ArgusApp.get_handler_by_name(App.dummy) == DummyApplication
