#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-31 09:38
# @version: 1.0
#
import collections
from typing import Dict


class DictUtil(object):
    @staticmethod
    def filter_values(map: Dict[object, collections.abc.Sequence], filter_func):
        if not map:
            return map
        keys = list(map.keys())
        for key in keys:
            value = list(filter(filter_func, map.pop(key)))
            if value:
                map[key] = value
        return map


__all__ = [
    'DictUtil'
]
