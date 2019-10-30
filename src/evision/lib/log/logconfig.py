"""An extended version of the log_settings module from zamboni:
https://github.com/jbalogh/zamboni/blob/master/log_settings.py
"""
from __future__ import absolute_import

import logging
import logging.handlers
import os.path as osp

from tornado.log import LogFormatter as TornadoLogFormatter

from . import dictconfig

__all__ = [
    'LogHandlers',
    'Loggers',
    'config'
]


class LogHandlers(object):
    def __init__(self):
        pass

    DEFAULT = 'default'
    TEST_DEFAULT = 'test_default'
    EXP_DEFAULT = 'exp_default'
    FILE = 'file'
    CONSOLE = 'console'
    NULL = 'null'


class Loggers(object):
    def __init__(self):
        pass

    DEFAULT = LogHandlers.DEFAULT
    TEST_DEFAULT = LogHandlers.TEST_DEFAULT
    CONSOLE = LogHandlers.CONSOLE
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
        except Exception:
            if isinstance(r, bytes):
                r = r.decode(self.encoding, 'replace')
        return r

    def format(self, record):
        return logging.Formatter(style='{').format(record)


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


def config(syslog_tag, loggers, log_level=logging.INFO, log_dir=None, show_console=False):
    if log_dir and not osp.exists(log_dir):
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
        return osp.join(log_dir, name) if log_dir else name

    def handler_config(name, extra=None):
        if not log_dir:
            return {
                '()': logging.StreamHandler,
                'formatter': 'tornado'
            }
        return {
            '()': logging.handlers.TimedRotatingFileHandler,
            'level': 'INFO',
            'when': 'midnight',
            'backupCount': 30,
            'formatter': 'tornado-plain',
            'filename': get_log_file(name, extra)
        }

    def format_tag(tag):
        return f'[{tag}] ' if tag else ''

    base_fmt = '[{levelname} {asctime}.{msecs:.03d} {filename}s:{lineno} - {funcName}] {message}'
    base_handlers = [LogHandlers.CONSOLE, LogHandlers.DEFAULT] \
        if show_console \
        else [LogHandlers.DEFAULT, ]

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
                'format': f'[%(asctime)s.%(msecs).03d] {format_tag(syslog_tag)}%(color)s[%(levelname)s] '
                          f'[%(filename)s:%(lineno)d - %(funcName)s]%(end_color)s %(message)s'
            },
            'tornado-plain': {
                '()': TornadoLogFormatter,
                'color': True,
                'datefmt': '%y-%m-%d %H:%M:%S',
                'format': f'[%(asctime)s.%(msecs).03d] {format_tag(syslog_tag)}[%(levelname)s] '
                          f'[%(filename)s:%(lineno)d - %(funcName)s] %(message)s'
            }
        },
        'handlers': {
            LogHandlers.NULL: {
                '()': NullHandler,
            },
            LogHandlers.CONSOLE: {
                '()': logging.StreamHandler,
                'formatter': 'tornado'
            },
            LogHandlers.DEFAULT: handler_config(LogHandlers.DEFAULT),
            'tornado.access': handler_config('tornado.access'),
            'tornado.application': handler_config('tornado.application'),
            'tornado.general': handler_config('tornado.general')
        },
        'loggers': {
            Loggers.DEFAULT: {
                'handlers': base_handlers
            },
            Loggers.CONSOLE: {
                'handlers': [LogHandlers.CONSOLE, ]
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


_default_inited = False
if not _default_inited:
    config('', loggers={}, log_level=logging.INFO, log_dir=None, show_console=False)
    _default_inited = True
