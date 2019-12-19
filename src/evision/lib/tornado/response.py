#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-15 14:52
# @version: 1.0

import logging

import tornado.web
from tornado.log import app_log

from evision.lib.log import logutil

logger = logutil.get_logger()

__all__ = [
    'Response',
    'ServerException',
]


class Response(object):
    """请求响应结构"""

    def __init__(self, status=0, message=None, result=None, extras=None):
        self.status = status
        self.message = '' if message is None else message
        if result is not None:
            self.data = result
        if extras and isinstance(extras, dict):
            if not hasattr(self, 'data') or not self.data:
                self.data = {}
            self.data.update(extras)

    def to_json(self):
        # o = bson_util._json_convert(self.__dict__)
        return tornado.escape.json_encode(self.__dict__)
        # return json.dumps(json_util._json_convert(self.__dict__),
        # default=json_util.default)
        # return json.dumps(self.result['icon'], default=json_util.default)
        # return json.dumps(self.__dict__, default=json_util.default)
        # return tornado.escape.json_encode(self.__dict__)

    def __str__(self):
        return self.to_json()


class ServerException(Exception):
    def __init__(self, status, msg):
        self.output = Response(status, message=msg)

    def __str__(self):
        return self.output


def _stack_context_handle_exception(type, value, traceback, handler):
    app_logger = logging.LoggerAdapter(app_log, extra={
    })
    if isinstance(value, ServerException):
        app_logger.error("%s" % str(value), exc_info=True)
        handler.write(str(value))
    elif isinstance(value, Exception):
        app_logger.error("%s" % str(value), exc_info=True)
        handler.write(Response(500, message=str(value)))
    # make request finish
    handler.finish()
    return True
