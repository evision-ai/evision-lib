# -*- coding: utf-8 -*-
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @version: 1.0

import logging
import uuid
from inspect import getfullargspec
from logging import Logger

from tornado import gen
from tornado.stack_context import StackContext, run_with_stack_context


class BraceMessage(object):
    def __init__(self, fmt, args, kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        if not self.args and not self.kwargs:
            return str(self.fmt)
        return str(self.fmt).format(*self.args, **self.kwargs)


class StyleAdapter(logging.LoggerAdapter):
    def __init__(self, logger):
        logging.LoggerAdapter.__init__(self, logger, None)
        self.logger = logger

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, log_kwargs = self.process(msg, kwargs)
            self.logger._log(level, BraceMessage(msg, args, kwargs), (),
                             **log_kwargs)

    def process(self, msg, kwargs):
        return msg, {key: kwargs[key]
                     for key in getfullargspec(self.logger._log).args[1:] if key in kwargs}


def get_logger(logger_name='api'):
    if logger_name not in Logger.manager.loggerDict:
        return StyleAdapter(logging.getLogger())
    return StyleAdapter(logging.getLogger(logger_name))


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
        request_id = uuid.uuid4().hex
        yield run_with_stack_context(StackContext(
            lambda: RequestIdContext(request_id)), lambda: func(*args, **kwargs))

    return _wrapper


__END__ = True
