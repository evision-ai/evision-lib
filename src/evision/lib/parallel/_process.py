#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-18 10:34
# @version: 1.0
#
import signal
from multiprocessing import Process

from evision.lib.log import logutil
from ._base import ParallelWrapperMixin

logger = logutil.get_logger()

__all__ = [
    'ProcessWrapper'
]


class ProcessWrapper(ParallelWrapperMixin, Process):
    def __init__(self, name=None, paths=None,
                 answer_sigint=False, answer_sigterm=False,
                 *args, **kwargs):
        self._paths = paths

        self.answer_sigint = answer_sigint
        self.answer_sigterm = answer_sigterm

        self._update_sys_path()

        Process.__init__(self, name=name, args=args, kwargs=kwargs)
        ParallelWrapperMixin.__init__(self, *args, **kwargs)

    def process(self):
        raise NotImplementedError

    def init(self):
        if self.answer_sigint:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        if self.answer_sigterm:
            signal.signal(signal.SIGINT, self._sig_kill_handler)
            signal.signal(signal.SIGTERM, self._sig_kill_handler)

    def _sig_kill_handler(self, sig, frame):
        logger.info('[{}] Stopping with signal={}, frame={}',
                    self.name, sig, frame)
        self._stop_event.set()
        if self._ended:
            return
        raise SystemExit()

    def _update_sys_path(self):
        if not self._paths:
            return
        import sys
        import os

        _path = self._paths
        assert isinstance(_path, str)
        _path = _path.split(':') if ':' in _path else [_path, ]
        _path = [os.path.abspath(os.path.expanduser(_)) for _ in _path]
        [sys.path.insert(0, _) for _ in _path[::-1]]
        logger.info(f'[{self.name}] Paths updated to: {sys.path}')
