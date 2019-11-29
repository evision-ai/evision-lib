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


class GroupType(IntEnum):
    # 黑名单
    BLACKLIST = 1
    # 访客
    VISITOR = 2
    # 内部人员
    INTERNAL = 3
    # 重要人员
    VIP = 4
    # 管理人员
    MANAGEMENT = 99
