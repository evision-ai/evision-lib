#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-12 14:48
# @version: 1.0
#
from enum import IntEnum
from typing import Any

from pydantic import BaseModel

__all__ = [
    'TypeUtil',
    'ValueAsStrIntEnum',
    'BaseModelWithExtras'
]


class TypeUtil(object):
    @staticmethod
    def is_subclass(class_: type, super_class):
        """判断 obj 是否是 cls 的子类"""
        if not class_:
            return False
        if not isinstance(class_, type):
            class_ = type(class_)
        if class_ is super_class:
            return True
        return issubclass(class_, super_class)

    @staticmethod
    def list_subclasses(class_, recursive=True, include_self=True):
        """ List subclasses inherited from current type

        :param class_: provided type
        :param recursive: where searching recursively
        :param include_self: whether including provided type
        :return: set of subclass types
        """
        if not class_:
            return None
        if not isinstance(class_, type):
            class_ = type(class_)
        _subclasses = set(class_.__subclasses__())
        if _subclasses and recursive:
            _subclasses = _subclasses.union(
                type_
                for subclass in _subclasses
                for type_ in TypeUtil.list_subclasses(subclass)
            )
        if include_self:
            _subclasses.add(class_)
        return _subclasses


class ValueAsStrIntEnum(IntEnum):
    """Override `__str__` of `IntEnum`, returns value of enum
    """

    def __str__(self):
        return str(self.value)


class BaseModelWithExtras(BaseModel):
    def __init__(self, **data: Any):
        extra = data.pop('extra') if 'extra' in data else {}
        extra_keys = set(data.keys()) - set(self.__fields__.keys())
        extra.update({key: data.pop(key) for key in extra_keys})
        super().__init__(extra=extra, **data)

    class Config():
        arbitrary_types_allowed = True
