#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-16 19:33
# @version: 1.0


class FailureCountMixin(object):
    """提供服务失败次数记录及重置的功能"""

    def __init__(self):
        self._fail_count = 0
        self.__listeners = {}

    def add_listener(self, listener):
        if not isinstance(listener, FailureCountMixin):
            return
        self.__listeners[id(listener)] = listener

    def remove_listener(self, listener):
        if not isinstance(listener, FailureCountMixin):
            return
        listener_id = id(listener)
        if listener_id in self.__listeners:
            self.__listeners.pop(listener_id)

    def reset_failure_count(self):
        self._fail_count = 0
        for listener in self.__listeners.values():
            listener.reset_failure_count()

    def accumulate_failure_count(self):
        if not hasattr(self, '_fail_count'):
            self._fail_count = 0
        self._fail_count += 1

    @property
    def failure_count(self):
        return 0 if not hasattr(self, '_fail_count') else self._fail_count

    def check_failure(self, threshold):
        return self.failure_count > threshold

    def try_restore(self, threshold=10, action=None):
        """判断是否从异常状态恢复"""
        if self.failure_count < threshold:
            return False
        if action and self.failure_count % threshold == 0:
            action()
        return True
