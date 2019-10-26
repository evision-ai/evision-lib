#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-12 12:54
# @version: 1.0

import base64

import peewee

__all__ = [
    'CompatibleBlobField'
]


class CompatibleBlobField(peewee.BlobField):
    """二进制列封装"""

    def db_value(self, value):
        if type(value) is str:
            value = peewee.sqlite3.Binary(
                base64.decodebytes(str.encode(value)))
        return value
