#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-12-03 19:15
# @version: 1.0
#
from evision.argus.constants.resource import ImageSourceType
from evision.argus.video.schema import ImageSourceCreateConfig


def test_image_source_create_config():
    source_uri = 'rtsp://'
    config = ImageSourceCreateConfig(source_uri=source_uri)
    assert config.source_key == (source_uri, ImageSourceType.IP_CAMERA)
    config = ImageSourceCreateConfig(source_type=ImageSourceType.USB_CAMERA, source_uri='0')
    assert config.source_key == (0, ImageSourceType.USB_CAMERA)

    config = ImageSourceCreateConfig(source_type=1, source_uri=source_uri)
    assert config.source_key == (source_uri, ImageSourceType.IP_CAMERA)
    config = ImageSourceCreateConfig(source_type=2, source_uri='0')
    assert config.source_key == (0, ImageSourceType.USB_CAMERA)
