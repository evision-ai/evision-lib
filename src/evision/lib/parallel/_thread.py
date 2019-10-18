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


class ThreadWrapper(Thread, ParallelWrapperMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def stop(self):
        if self._ended:
            logger.warn('[{}] Already stopped', self.name)
            return
        # set stop event
        try:
            self._stop_event.set()
            return
        except Exception as e:
            logger.error(f'[{self.name}] Failed setting stop event', e)
