#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-18 10:34
# @version: 1.0
#
from threading import Thread

from evision.lib.log import logutil
from ._base import ParallelWrapperMixin

logger = logutil.get_logger()

__all__ = [
    'ThreadWrapper'
]


class ThreadWrapper(ParallelWrapperMixin, Thread):
    def __init__(self, name=None, *args, **kwargs):
        Thread.__init__(self, name=name, args=args, kwargs=kwargs)
        ParallelWrapperMixin.__init__(self, *args, **kwargs)

    def process(self):
        raise NotImplementedError
