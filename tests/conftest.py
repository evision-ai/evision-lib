# -*- coding: utf-8 -*-

"""Module for pytest fixtures"""
import logging

from evision.lib.log import logconfig
from evision.lib.log.logconfig import Loggers

# override default logger
Loggers.DEFAULT = Loggers.TEST_DEFAULT
logconfig.config('TEST', {}, log_level=logging.DEBUG, show_console=True)
