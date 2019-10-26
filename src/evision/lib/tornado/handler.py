# -*- coding: utf-8 -*-
# API处理逻辑基础结构
#

import cv2
import numpy as np
import tornado.web
from webargs import ValidationError
from webargs.tornadoparser import HTTPError

from evision.lib.constant import Message, Status
from evision.lib.context import RequestIdContext, with_request_id
from evision.lib.log import logutil
from evision.lib.tornado.response import Response

logger = logutil.get_logger()

__all__ = [
    'BaseHandler',
    'TestIndexHandler'
]


class BaseHandler(tornado.web.RequestHandler):
    """A class to collect common handler methods - all other handlers should
    subclass this one.

    @apiDefine CommonResponse 通用响应参数

    @apiSuccess {number} status 请求状态
    @apiSuccess {string} message 请求提示信息
    """
    __allow_origins = [
    ]

    @with_request_id
    async def initialize(self):
        """
        make the request id context is available

        :return:
        """
        pass

    async def prepare(self):
        """

        before real handler runs

        1. update request id

        :return:
        """
        request_id = self.request.headers.get("X-Request-ID")
        if request_id:
            RequestIdContext.set(request_id)
        else:
            self.set_header("X-Request-ID", RequestIdContext.get())

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin",
                        self.request.headers.get("Origin", ""))
        self.set_header("Access-Control-Allow-Methods",
                        "POST, GET, PUT, PATCH, DELETE, HEAD, OPTIONS")
        self.set_header("Pragma", "no-cache")
        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.set_header('Access-Control-Allow-Headers',
                        'Content-Type, Access-Control-Allow-Headers, '
                        'Authorization, X-Requested-With, Cache-Control')

    def _set_ssl(self):
        """
        设置协议 http 或者 https

        :return:
        """
        if self.request.headers.get("Ssl") == "on":
            self.https = True
            self.scheme = "https://"
        else:
            self.https = False
            self.scheme = "http://"

    def data_received(self, chunk):
        pass

    def load_json(self):
        """Load JSON from the request body and store them in
        self.request.arguments, like Tornado does by default for POSTed form
        parameters.

        If JSON cannot be decoded, raises an HTTPError with status 400.
        """
        try:
            self.request.arguments = tornado.escape.json_decode(self.request.body)
        except ValueError:
            msg = "Could not decode JSON: %s" % self.request.body
            logger.debug(msg)
            raise tornado.web.HTTPError(400, msg)

    def get_json_argument(self, name: str, default=None):
        """Find and return the argument with key 'name' from JSON request data.
        Similar to Tornado's get_argument() method.
        """
        self.load_json()
        if name not in self.request.arguments:
            if default is self._ARG_DEFAULT:
                msg = "Missing argument '%s'" % name
                logger.debug(msg)
                raise tornado.web.HTTPError(400, msg)
            logger.debug('Using {}={}, arguments={}',
                         name, default, self.request.arguments)
            return default
        arg = self.request.arguments[name]
        logger.debug('Found {}: {} in JSON arguments', name, arg)
        return arg

    def get_json_arguments(self, *fields):
        """获取JSON参数中的字段值"""
        _values = []
        _missed_values = []
        try:
            _arguments_json = tornado.escape.json_decode(self.request.body)
            for _field in fields:
                if _field not in _arguments_json:
                    _missed_values.append(_field)
            if len(_missed_values) > 0:
                self.finish('failed to get arguments: ' + str(_missed_values))
            for _field in fields:
                _values.append(_arguments_json[_field])
            return _values
        except Exception as e:
            self.finish('unable to get arguments: ' + str(e))

    def get_arguments(self, *fields):
        """获取请求参数"""
        _values = []
        _missed_values = []
        try:
            for _field in fields:
                _value = self.get_argument(_field, None)
                if _value is None:
                    _missed_values.append(_field)
            if len(_missed_values) > 0:
                self.finish_error(status=Status.FAILED,
                                  message='Failed get arguments: ' + str(_missed_values))
            for _field in fields:
                _values.append(self.get_argument(_field, None))
            return _values
        except Exception as e:
            self.finish('unable to get arguments: ' + str(e))

    def finish_response(self, status=Status.OK, message=Message.OK, result=None,
                        finish=True, **extras):
        """结束请求,发送响应

        :param status: 请求响应状态
        :param message: 请求响应消息
        :param result: 请求响应结果
        :param finish: 是否结束请求
        :param extras: 请求响应中其他部分
        """
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        _response = Response(status, message, result, extras)
        self.write(_response.to_json())
        if finish:
            self.finish()

    def finish_dict_response(self, ret_dict, finish=True):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')

        self.write(tornado.escape.json_encode(ret_dict))
        if finish:
            self.finish()

    def finish_error(self, _error=None,
                     error_code=Status.FAILED, message=Message.FAILED,
                     result=None, to_log=True, finish=True, **kwargs):
        """标识该请求发生错误,发送响应

        :param _error: 封装的错误信息
        :param error_code: 错误代码
        :param message: 请求响应消息
        :param result: 请求响应结果
        :param to_log: 是否保存日志信息
        :param finish: 是否结束请求
        :param kwargs: 请求响应中其他部分
        """
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        if _error is not None:
            error_code = _error.code
            message = _error.message

        if to_log:
            logger.error('Error {}: {} - {}, extras={}',
                         error_code, message, str(result), kwargs)
        response = Response(error_code, message=message, result=result,
                            extras=kwargs)
        self.write(response.to_json())
        if finish:
            self.finish()

    def write_error(self, status_code, **kwargs):
        """Write errors as JSON."""
        self.set_header('Content-Type', 'application/json')
        if 'exc_info' in kwargs:
            type_, value, traceback = kwargs['exc_info']
            if hasattr(value, 'messages'):
                self.write({'errors': value.messages})
                self.finish()

    def _get(self, *args, **kwargs):
        pass

    def _post(self, *args, **kwargs):
        pass

    def __handle(self, _method, *args, **kwargs):
        """请求处理过程,封装错误处理"""
        try:
            _method(*args, **kwargs)
        except ValidationError as ve:
            logger.exception('Validation error: {}', ve)
            self.finish_error(error_code=ve.status_code,
                              message='ValidationError',
                              detail=ve.messages)
        except HTTPError as he:
            logger.exception('HTTP error: {}', he)
            self.finish_error(error_code=he.status_code,
                              message='Failed parsing arguments',
                              detail=he.messages)
        except AssertionError as ae:
            logger.exception('Assertion error: {}', ae)
            self.finish_error(message='Assertion failed', detail=str(ae))
        except AttributeError as ae:
            logger.exception('Attribute error: {}', ae)
            self.finish_error(message='Invalid arguments', detail=str(ae))
        except Exception as e:
            logger.exception('Request failed: {}', e)
            self.finish_error(message=str(e))

    def get(self, *args, **kwargs):
        self.__handle(self._get, *args, **kwargs)

    def post(self, *args, **kwargs):
        self.__handle(self._post, *args, **kwargs)

    def options(self, *args, **kwargs):
        self.finish()

    def get_image_file(self, file='file'):
        file = self.request.files[file][0]
        filename = file['filename']
        content = np.frombuffer(file['body'], np.uint8)
        image = cv2.imdecode(content, cv2.IMREAD_COLOR)
        return image, filename


class TestIndexHandler(BaseHandler):
    # @tornado.web.authenticated
    def get(self):
        self.render('index.html')
