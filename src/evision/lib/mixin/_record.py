#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-16 19:30
# @version: 1.0
#
import time

import numpy as np

from evision.lib.log import LogHandlers, logutil

logger = logutil.get_logger(LogHandlers.DEFAULT)

__all__ = [
    'HistoryRecorderMixin',
    'SimilarHistoryRecorderMixin'
]


class HistoryRecorderMixin(object):
    """提供精确匹配的历史记录去重功能"""
    _last_seen_map: dict = {}
    _key_field: str = 'person_id'
    _keep_recent: bool = False
    _expiry_time = 12

    def __init__(self, index_field=None, keep_recent=None, expiry_time=None,
                 **kwargs):
        """ Record process history and determine whether to process current task

        :param index_field: index field name of task
        :param keep_recent: process most recent tasks or drop frequent tasks
        :param expiry_time: expiry time of record history
        """
        super().__init__(**kwargs)
        self._last_seen_map = {}
        self.key_field = index_field if index_field else self._key_field
        self.keep_recent = keep_recent if keep_recent is not None else self._keep_recent
        self.expiry_time = expiry_time if expiry_time else self._expiry_time

    def update_show_time(self, key):
        """更新对象的出现时间"""
        self._last_seen_map[key] = time.time()

    def elapsed_from_last(self, key):
        """同一对象距上次出现的时间间隔"""
        return time.time() - self._last_seen_map[key] \
            if key in self._last_seen_map \
            else 0

    def should_keep_recent(self, key):
        """是否保存近期历史"""
        return key in self._last_seen_map and self.elapsed_from_last(key) < self.expiry_time

    def should_filter_recent(self, key):
        """是否应该丢弃近期历史"""
        return key not in self._last_seen_map or self.elapsed_from_last(key) > self.expiry_time

    def meet_frequency_requirement_by_value(self, key):
        """对象是否满足出现频率要求"""
        _will_process = self.should_keep_recent(key) \
            if self.keep_recent \
            else self.should_filter_recent(key)
        if _will_process:
            logger.info('Update last seen time for key={}', key)
            self.update_show_time(key)
        else:
            logger.info('Filter this time for key={}, last seen={}',
                        key, self._last_seen_map.get(key, None))
        return _will_process

    def meet_frequency_requirement(self, task):
        value = getattr(task, self.key_field)
        return self.meet_frequency_requirement_by_value(value)

    def reset_show_time(self, task):
        value = getattr(task, self.key_field)
        if value in self._last_seen_map:
            self._last_seen_map.pop(value)


class SimilarHistoryRecorderMixin(HistoryRecorderMixin):
    """提供基于距离匹配的历史记录去重功能"""
    _bias = 0.5

    def __init__(self, index_field=None, keep_recent=None,
                 expiry_time=None, bias=None, **kwargs):
        HistoryRecorderMixin.__init__(self, index_field, keep_recent, expiry_time, **kwargs)
        self.bias = bias if bias else self._bias

    def get_most_similar_key(self, key):
        """获取当前缓存映射中与指定对象最相似的对象

        TODO: 距离计算可以尝试切换成cdist
        """
        if not self._last_seen_map:
            return None
        candidate = None
        distance = None
        for exist_key in self._last_seen_map.keys():
            cur_distance = np.sum(np.square(np.array(exist_key), key))
            if cur_distance > self.bias:
                continue
            if distance is None or cur_distance < distance:
                candidate, distance = exist_key, cur_distance
        return candidate

    def meet_frequency_requirement_by_value(self, key):
        nearest_key = self.get_most_similar_key(key)
        if nearest_key is None:
            self.update_show_time(tuple(key))
            return True

        will_process = self.should_keep_recent(nearest_key) \
            if self.keep_recent \
            else self.should_filter_recent(nearest_key)
        if not will_process:
            logger.info('Filter this feature for last seen={}',
                        self._last_seen_map.get(nearest_key, None))
        else:
            self.update_show_time(nearest_key)
        return will_process
