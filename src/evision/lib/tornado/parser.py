# -*- coding: utf-8 -*-
#
# Copyright 2018 eVision.ai Inc. All Rights Reserved.
#
# 参数解析封装
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-06-19 17:03
# @version: 1.0
#

from webargs import core
from webargs import tornadoparser
from webargs.tornadoparser import TornadoParser

__all__ = [
    'parser'
]


def _get_value(d, name, field):
    """Handle gets from 'multidicts' made of lists

    It handles cases: ``{"key": [value]}`` and ``{"key": value}``
    """
    multiple = core.is_multiple(field)
    value = d.get(name, core.missing)
    if not value:
        return core.missing
    if multiple and value is not core.missing:
        return [tornadoparser.decode_argument(v, name)
                if isinstance(v, tornadoparser.basestring) else v
                for v in value]
    ret = value
    if value and isinstance(value, (list, tuple)):
        ret = value[0]
    if isinstance(ret, tornadoparser.basestring):
        if not ret:
            return core.missing
        return tornadoparser.decode_argument(ret, name)
    else:
        return ret


class ArgumentsParser(TornadoParser):
    def __init__(self, *args, **kwargs):
        super(ArgumentsParser, self).__init__(*args, **kwargs)
        self.json = None

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return _get_value(req.query_arguments, name, field)

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        return _get_value(req.body_arguments, name, field)

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return _get_value(req.headers, name, field)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return _get_value(req.files, name, field)


parser = ArgumentsParser()
