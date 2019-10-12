#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-12 13:05
# @version: 1.0


class PropertiesNotProvided(ValueError):
    """未提供初始化对象所需属性"""

    def __init__(self, missing):
        ValueError.__init__(self, f'Properties not provided: {missing}')


class HttpNoResponse(Exception):
    """调用外部API无法获取响应"""

    def __init__(self):
        Exception.__init__(self, 'No response')


class HttpInvalidStatus(Exception):
    """调用外部API获取的状态码无效"""

    def __init__(self, status_code=None):
        Exception.__init__(self, f'Invalid response, code={status_code}')


class PropertySettingNotAllowed(ValueError):
    """不允许直接设置属性"""

    def __init__(self, value_name=None):
        ValueError.__init__(
            self, f'Setting properties of {value_name} is not allowed')
