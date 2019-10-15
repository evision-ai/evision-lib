# -*- coding: utf-8 -*-

"""Module for pytest fixtures"""
import logging

from evision.lib.log import logconfig
from evision.lib.log.logconfig import Loggers

# override default logger
Loggers.DEFAULT = Loggers.TEST_DEFAULT
SYSLOG_FACILITY = logging.handlers.SysLogHandler.LOG_LOCAL2
logconfig.initialize_logging('TEST', SYSLOG_FACILITY, {},
                             logging.DEBUG, show_console=True)
