# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-06-20 11:58
# @version: 1.0
#
import json
import urllib.parse

from tornado.httpclient import AsyncHTTPClient
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase

from evision.lib.constant import Keys
from evision.lib.log import logutil
from evision.lib.log.logconfig import Loggers

logger = logutil.get_logger(Loggers.SERVICE_DEFAULT)


class AsyncTest(AsyncTestCase):
    def test_http_fetch(self):
        client = AsyncHTTPClient()
        client.fetch("http://www.tornadoweb.org/", self.handle_fetch)
        self.wait()

    def handle_fetch(self, response):
        # Test contents of response (failures and exceptions here
        # will cause self.wait() to throw an exception and end the
        # test).
        # Exceptions thrown here are magically propagated to
        # self.wait() in test_http_fetch() via stack_context.
        self.assertIn("FriendFeed", response.body.decode())
        self.stop()


class BaseTestCase(AsyncHTTPTestCase):
    _url = None

    def get_app(self):
        raise NotImplementedError

    def _check_response(self, method, response, allow_data_none, data_keys):
        self.assertEqual(response.code, 200)
        result = json.loads(response.body)
        assert result is not None
        logger.info('[{}] {}: {}', method, self._url, result)

        if not allow_data_none:
            assert Keys.DATA in result and result[Keys.DATA] is not None

            if data_keys:
                for key in data_keys:
                    assert key in result[Keys.DATA]

        return result

    def _get(self, allow_data_none=False, data_keys=None):
        response = self.fetch(self._url, method='GET')
        return self._check_response('GET', response, allow_data_none, data_keys)

    def _post(self, params=None, allow_data_none=False, data_keys=None,
              encode=True):
        if params is None:
            params = {}
        body = urllib.parse.urlencode(params) if encode else params
        response = self.fetch(self._url, method='POST', body=body)
        return self._check_response('POST', response, allow_data_none, data_keys)
