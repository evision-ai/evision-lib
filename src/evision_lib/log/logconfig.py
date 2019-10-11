"""An extended version of the log_settings module from zamboni:
https://github.com/jbalogh/zamboni/blob/master/log_settings.py
"""
from __future__ import absolute_import

import logging
import logging.handlers
import os.path as osp

from tornado.log import LogFormatter as TornadoLogFormatter
from . import dictconfig


class LogHandlers:
    def __init__(self):
        pass

    SERVICE_DEFAULT = 'default'
    TEST_DEFAULT = 'test_default'
    EXP_DEFAULT = 'exp_default'
    FILE = 'file'
    CONSOLE = 'console'
    NULL = 'null'


class Loggers:
    def __init__(self):
        pass

    SERVICE_DEFAULT = LogHandlers.SERVICE_DEFAULT
    UTIL = 'util'


class UTF8SafeFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, encoding='utf-8'):
        logging.Formatter.__init__(self, fmt, datefmt)
        self.encoding = encoding

    def formatException(self, e):
        r = logging.Formatter.formatException(self, e)

        # types in PY3 do not have attribute StringType
        try:
            if isinstance(r, str):
                r = bytes(r).decode(self.encoding, 'replace')  # Convert to unicode
        except:
            if isinstance(r, bytes):
                r = r.decode(self.encoding, 'replace')
        return r

    def format(self, record):
        return logging.Formatter(style='{').format(record)


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


def initialize_logging(syslog_tag, syslog_facility, loggers,
                       log_level=logging.INFO, use_syslog=False,
                       log_dir=None, log_file=None, show_console=False):
    if not osp.exists(log_dir):
        import os

        os.makedirs(log_dir)

    def get_log_file(name, extra=None):
        ###################################
        # log from all ports ro one file
        ###################################
        # if port is not None:
        #     name += '_' + str(port)
        if extra is not None:
            name += '_' + str(extra)
        name += '.log'
        return osp.join(log_dir, name)

    base_fmt = '[{levelname} {asctime}.{msecs:.03d} {filename}s:{lineno} - {funcName}] {message}'
    base_handlers = [LogHandlers.CONSOLE, LogHandlers.SERVICE_DEFAULT] \
        if show_console \
        else [LogHandlers.SERVICE_DEFAULT]

    cfg = {
        'version': 1,
        'filters': {},
        'formatters': {
            'debug': {
                '()': UTF8SafeFormatter,
                'datefmt': '%H:%M:%S',
                'format': '[%s] %s' % (syslog_tag, base_fmt),
            },
            'prod': {
                '()': UTF8SafeFormatter,
                'datefmt': '%H:%M:%S',
                'format': base_fmt,
            },
            'tornado': {
                '()': TornadoLogFormatter,
                'color': True,
                'datefmt': '%y-%m-%d %H:%M:%S',
                'format': '[%(asctime)s.%(msecs).03d] [{}] %(color)s[%(levelname)s] [%(filename)s:%(lineno)d - '
                          '%(funcName)s]%(end_color)s %(message)s'.format(syslog_tag)
            },
        },
        'handlers': {
            LogHandlers.SERVICE_DEFAULT: {
                '()': logging.handlers.TimedRotatingFileHandler,
                'level': 'INFO',
                'when': 'midnight',
                'backupCount': 30,
                'formatter': 'tornado',
                'filename': get_log_file(LogHandlers.SERVICE_DEFAULT)
            },
            LogHandlers.CONSOLE: {
                '()': logging.StreamHandler,
                'formatter': 'tornado'
            },
            LogHandlers.NULL: {
                '()': NullHandler,
            },
            'tornado.access': {
                '()': logging.handlers.TimedRotatingFileHandler,
                'level': 'INFO',
                'when': 'midnight',
                'formatter': 'tornado',
                'filename': get_log_file('tornado.access')
            },
            'tornado.application': {
                '()': logging.handlers.TimedRotatingFileHandler,
                'level': 'INFO',
                'when': 'midnight',
                'formatter': 'tornado',
                'filename': get_log_file('tornado.application')
            },
            'tornado.general': {
                '()': logging.handlers.TimedRotatingFileHandler,
                'level': 'INFO',
                'when': 'midnight',
                'formatter': 'tornado',
                'filename': get_log_file('tornado.general')
            }
        },
        'loggers': {
            LogHandlers.SERVICE_DEFAULT: {
                'handlers': base_handlers
            },
            'tornado.access': {
                'handlers': ['tornado.access']
            },
            'tornado.application': {
                'handlers': ['tornado.application']
            },
            'tornado.general': {
                'handlers': ['tornado.general']
            }
        },
        'root': {
            'handlers': base_handlers
        }
    }

    for key, value in loggers.items():
        cfg[key].update(value)

    # Set the level and handlers for all loggers.
    for logger in cfg['loggers'].values():
        if 'handlers' not in logger:
            logger['handlers'] = [LogHandlers.CONSOLE, ]
        if 'level' not in logger:
            logger['level'] = log_level
        if 'propagate' not in logger:
            logger['propagate'] = False

    # logging.info('Logging config: {}'.format(cfg))
    if not cfg:
        return
    dictconfig.dictConfig(cfg)
