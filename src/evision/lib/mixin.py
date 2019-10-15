# -*- coding: utf-8 -*-
#
# Copyright 2018 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-06-20 15:27
# @version: 1.0
#
"""可挂载功能封装的Mixin"""

import itertools
import time

import numpy as np

from evision.lib.constant import Keys
from evision.lib.decorator import class_property
from evision.lib.error import PropertiesNotProvided
from evision.lib.log import LogHandlers, logutil
from evision.lib.util import TypeUtil

logger = logutil.get_logger(LogHandlers.DEFAULT)


class SaveAndLoadConfigMixin(object):
    """提供基于配置存储与新建实例的功能"""
    _config_parser = None

    def get_config(self):
        """获取恢复该对象相关的配置，需要指明section名称

        :return: section, configuration dict
        :rtype: str, dict
        """
        pass

    def save_config(self):
        """保存当前对象的配置"""
        if not self._config_parser:
            raise ValueError('No configuration parser')
        section, config_map = self.get_config()
        if not section:
            return

        self._config_parser.replace_section(section, config_map, save=True)
        return section, config_map

    def load_config(self):
        """根据提供配置恢复对象"""
        pass

    def remove_config(self):
        pass


class PropertyHandlerMixin(SaveAndLoadConfigMixin):
    """ Mixin for handling properties

    Attributes:
        required_properties: required property names
        optional_properties: optional property names
        handler_alias: handler alias
            Classes extends this mixin but set no `_handler_alias` are not
            exposed to WebAPI, and are set with unique aliases
    """

    # required properties
    required_properties = []

    # optional properties
    optional_properties = []

    # handler alias
    handler_alias = None

    @staticmethod
    def check_property_map(value, *property_names):
        missing = []
        for property_name in property_names:
            if property_name not in value:
                missing.append(property_name)
        if not missing:
            raise PropertiesNotProvided(missing)

    @property
    def visible(self):
        return self.handler_alias is not None

    @property
    def alias(self):
        return self.handler_alias

    def get_properties(self):
        _properties = {}
        for property_name in itertools.chain(self.required_properties,
                                             self.optional_properties):
            _properties[property_name] = getattr(self, property_name)
        return _properties

    def set_properties(self, value):
        PropertyHandlerMixin.check_property_map(value, *self.required_properties)
        for property_name in self.required_properties:
            setattr(self, property_name, value[property_name])
        for property_name in self.optional_properties:
            if property_name in value:
                setattr(self, property_name, value[property_name])
        self._reload()

    def _reload(self):
        """ Reload function on properties reset
        """
        pass

    properties = property(get_properties, set_properties)

    def describe(self):
        return {self.handler_alias: self.get_properties()}

    @property
    def alias_and_properties(self):
        return {
            Keys.NAME: self.handler_alias,
            Keys.PROPERTIES: self.properties
        }

    @class_property
    def available_handler_classes(cls):
        if hasattr(cls, '_handler_classes'):
            return getattr(cls, '_handler_classes')
        _handler_classes = {}

        subclasses = TypeUtil.list_subclasses(cls)
        for subclass in subclasses:
            assert isinstance(subclass, PropertyHandlerMixin)
            if not hasattr(subclass, 'handler_alias') \
                or subclass.handler_alias is None:
                logger.info('Skip {} for no alias set', subclass)
                continue
            _handler_classes[subclass.handler_alias] = subclass

        setattr(cls, '_handler_classes', _handler_classes)
        return _handler_classes

    @class_property
    def available_handlers(cls):
        if hasattr(cls, '_available_handlers'):
            return getattr(cls, '_available_handlers')
        _available_handlers = {}

        subclasses = TypeUtil.list_subclasses(cls)
        for subclass in subclasses:
            if not TypeUtil.is_subclass(subclass, PropertyHandlerMixin):
                continue
            if not hasattr(subclass, 'handler_alias') \
                or subclass.handler_alias is None:
                logger.info('Skip {} for no alias set', subclass)
                continue
            _available_handlers[subclass.handler_alias] = {
                'required': subclass.required_properties,
                'optional': subclass.optional_properties
            }

        setattr(cls, '_available_handlers', _available_handlers)
        return _available_handlers


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
        return key in self._last_seen_map \
               and self.elapsed_from_last(key) < self.expiry_time

    def should_filter_recent(self, key):
        """是否应该丢弃近期历史"""
        return key not in self._last_seen_map \
               or self.elapsed_from_last(key) > self.expiry_time

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


__all__ = [
    'PropertyHandlerMixin',
    'SaveAndLoadConfigMixin',
    'HistoryRecorderMixin',
    'SimilarHistoryRecorderMixin',
    'FailureCountMixin'
]
