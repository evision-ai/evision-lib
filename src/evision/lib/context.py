#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-23 09:46
# @version: 1.0
#

from tornado import gen
from tornado.stack_context import StackContext
from tornado.stack_context import run_with_stack_context

from evision.lib.util import CacheUtil

__REQUEST_ID_LENGTH__ = 32

__all__ = [
    'RequestIdContext',
    'with_request_id'
]


class RequestIdContext:
    class _Context:
        def __init__(self, request_id=0):
            self.request_id = request_id

        def __eq__(self, other):
            return self.request_id == other.request_id

    _data = _Context()

    def __init__(self, request_id):
        self.current_data = RequestIdContext._Context(request_id=request_id)
        self.old_data = None

    @classmethod
    def set(cls, request_id):
        cls._data.request_id = request_id

    @classmethod
    def get(cls):
        return cls._data.request_id

    def __enter__(self):
        if RequestIdContext._data == self.current_data:
            return

        self.old_context_data = RequestIdContext._Context(
            request_id=RequestIdContext._data.request_id,
        )

        RequestIdContext._data = self.current_data

    def __exit__(self, exc_type, exc_value, traceback):
        if self.old_data is not None:
            RequestIdContext._data = self.old_data


def with_request_id(func):
    @gen.coroutine
    def _wrapper(*args, **kwargs):
        request_id = CacheUtil.random_string(__REQUEST_ID_LENGTH__)
        yield run_with_stack_context(StackContext(
            lambda: RequestIdContext(request_id)), lambda: func(*args, **kwargs))

    return _wrapper
