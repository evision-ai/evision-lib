#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-14 15:10
# @version: 1.0
#
import ast
import json
from datetime import datetime

import peewee

from evision.lib.decorator import CachedProperty

__all__ = [
    'BaseModel',
    'TimestampedModel'
]


class BaseModel(peewee.Model):
    """数据库表结构封装"""

    class Meta:
        database = peewee.Proxy()

    @classmethod
    def init(cls):
        cls._meta.database.create_tables([cls, ])

    @CachedProperty
    def extra_info(self):
        return ast.literal_eval(self.extras) if getattr(self, 'extras', None) \
            else {}

    def __str__(self):
        try:
            return json.dumps(self.__dict__)
        except Exception:
            return str(self.__dict__)


class TimestampedModel(BaseModel):
    create_time = peewee.DateTimeField()
    update_time = peewee.DateTimeField()

    def save(self, *args, **kwargs):
        now = datetime.now()
        if self._pk is None or not self.create_time:
            self.create_time = now
        self.update_time = now
        return super(TimestampedModel, self).save(*args, **kwargs)
