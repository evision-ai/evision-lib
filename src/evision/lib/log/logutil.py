# -*- coding: utf-8 -*-
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @version: 1.0

import logging
from inspect import getfullargspec
from logging import Logger

from evision.lib.log.logconfig import Loggers

__all__ = [
    'get_logger',
    'BraceMessage',
    'StyleAdapter'
]


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


def get_logger(logger_name=Loggers.DEFAULT):
    if logger_name not in Logger.manager.loggerDict:
        return StyleAdapter(logging.getLogger())
    return StyleAdapter(logging.getLogger(logger_name))


__END__ = True
