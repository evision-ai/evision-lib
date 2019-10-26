#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-16 19:29
# @version: 1.0

import itertools

from evision.lib.constant import Keys
from evision.lib.decorator import class_property
from evision.lib.error import PropertiesNotProvided
from evision.lib.log import LogHandlers, logutil
from evision.lib.util import TypeUtil

logger = logutil.get_logger(LogHandlers.DEFAULT)

__all__ = [
    'SaveAndLoadConfigMixin',
    'PropertyHandlerMixin'
]


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
            if not hasattr(subclass, 'handler_alias') or subclass.handler_alias is None:
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
            if not hasattr(subclass, 'handler_alias') or subclass.handler_alias is None:
                logger.info('Skip {} for no alias set', subclass)
                continue
            _available_handlers[subclass.handler_alias] = {
                'required': subclass.required_properties,
                'optional': subclass.optional_properties
            }

        setattr(cls, '_available_handlers', _available_handlers)
        return _available_handlers
