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
    'BaseVersionedModel',
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


class BaseVersionedModel(BaseModel):
    """包含乐观锁的数据库表结构封装"""
    version = peewee.IntegerField(default=0)

    def save_optimistic(self):
        if not self.version:
            return self.save()  # Since this is an `INSERT`, just call regular save method.

        # Update any data that has changed and bump the version counter.
        field_data = dict(self._data)
        current_version = field_data.pop('version', 0)
        field_data = self._prune_fields(field_data, self.dirty_fields)
        if not field_data:
            raise ValueError('No changes have been made.')

        model_class = type(self)
        field_data['version'] = model_class.version + 1  # Atomic increment

        query = model_class.update(**field_data).where(
            (model_class.version == current_version) &
            (model_class.id == self.id))

        nrows = query.execute()
        if nrows == 0:
            # It looks like another process has updated the version number.
            raise peewee.PeeweeException('Conflict')  # Raise exception? Return False?
        else:
            self.version += 1  # Update in-memory version number.
            return nrows


class TimestampedModel(BaseModel):
    create_time = peewee.DateTimeField()
    update_time = peewee.DateTimeField()

    def save(self, *args, **kwargs):
        now = datetime.now()
        if self._pk is None or not self.create_time:
            self.create_time = now
        self.update_time = now
        return super(TimestampedModel, self).save(*args, **kwargs)
