#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-16 19:52
# @version: 1.0
#
import threading
import time

from evision.lib.log import logutil
from evision.lib.util import SysUtil

logger = logutil.get_logger()

__all__ = [
    'AtomicInteger', 'ParallelWrapperMixin'
]


class AtomicInteger(object):
    def __init__(self, value=0):
        self._value = value
        self._lock = threading.Lock()

    def add(self, value=1):
        with self._lock:
            self._value += value
            return self._value

    count = add

    def minus(self, value=1):
        with self._lock:
            self._value -= value
            return self._value

    @property
    def value(self):
        with self._lock:
            return self._value

    @value.setter
    def value(self, v):
        with self._lock:
            self._value = v


class ParallelWrapperMixin(object):
    """后台服务（进程或线程）公共方法封装"""

    def __init__(self, name=None, interval=None,
                 show_error=False, fail_on_error=False,
                 exclusive_init_lock=False, **kwargs):
        if not hasattr(self, 'name'):
            self.name = name
        self.interval = interval

        self.show_error = show_error
        self.fail_on_error = fail_on_error

        self._init_lock = exclusive_init_lock

        self._stop_event = threading.Event()
        self._stop_event.clear()

        self.__tick = AtomicInteger()
        self.__total_time = 0

        self._inited = False
        self._running = False
        self._ended = False

        self._init()

    def is_inited(self):
        return self._inited

    def _init(self):
        """初始化方法"""
        self._stop_event.clear()
        if self._inited:
            return
        try:
            if not self._init_lock:
                self.init()
            else:
                with self._init_lock:
                    self.init()
            self._inited = True
        except Exception:
            logger.exception('Failed initializing {}, type={}', self.name,
                             self.__class__)
            self._stop_event.set()

    def init(self):
        """环境准备等初始化工作"""
        pass

    def on_start(self):
        """业务相关初始化工作"""
        pass

    def run(self):
        if not self._inited:
            self._init()
        if not self.is_inited():
            logger.info(f'Job not inited, please call {self.__class__}.init() first')
            return
        SysUtil.disable_sys_stdin()

        try:
            if self._stop_event.is_set():
                return
            self.on_start()
        except Exception as e:
            logger.exception('Failed preparing {}, type={}',
                             self.name, self.__class__, e)
            self._stop_event.set()

        self._running = True
        while not self._stop_event.is_set():
            tick = time.perf_counter()
            try:
                self.process()
            except (KeyboardInterrupt, SystemExit):
                pass
            except Exception as e:
                if self.show_error:
                    logger.error(f'[{self.name}] Failed processing '
                                 f'{self.__class__}', e)
                if self.fail_on_error:
                    logger.error('[{}] Failed on error: {}', self.name, e)
                    break

            self.__tick.count()
            toc = time.perf_counter()
            elapsed = toc - tick
            if self.interval and self.interval > 0 and elapsed < self.interval:
                # logger.debug('Waiting for next tick, sleep {}s', max(self.interval - elapsed, 0))
                time.sleep(max(self.interval - elapsed, 0))
            self.__total_time += elapsed

        self._ended = True
        self._running = False
        logger.info('[{}] Finished with {} ticks', self.name, self.ticks)
        self.on_stop()

    def stop(self):
        if self._ended:
            logger.warn('[{}] Already stopped', self.name)
            return
        # set stop event
        try:
            self._stop_event.set()
            return
        except Exception as e:
            logger.exception(f'[{self.name}] Failed setting stop event', e)

    def on_stop(self):
        pass

    def reload(self):
        pass

    def process(self):
        raise NotImplementedError()

    def avg_time(self):
        """ avg handling time in millisecond """
        return self.__total_time / (self.__tick or 1)

    @property
    def ended(self):
        return self._ended

    @property
    def running(self):
        return self._running

    @property
    def ticks(self):
        return self.__tick.value
