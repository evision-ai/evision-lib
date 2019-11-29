#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-11-29 13:48
# @version: 1.0
#
from enum import IntEnum


class RecordType(IntEnum):
    # 检测记录
    DETECTION = 1
    # 匹配记录
    MATCH = 2
    # 属性识别记录
    PROPERTY = 3
