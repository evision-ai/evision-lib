#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-16 19:29
# @version: 1.0

import itertools
from enum import Enum
from typing import Dict, List, Type, Union

from evision.lib.constant import Keys
from evision.lib.decorator import classproperty, classproperty_support
from evision.lib.error import PropertiesNotProvided
from evision.lib.log import LogHandlers, logutil
from evision.lib.util.types import TypeUtil

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


@classproperty_support
class PropertyHandlerMixin(SaveAndLoadConfigMixin):
    """ Mixin for handling properties

    Attributes:
        required_properties: required property names
        optional_properties: optional property names
        handler_alias: handler alias
            Classes extends this mixin but set no `handler_alias` are not
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
            return
        raise PropertiesNotProvided(missing)

    @classproperty
    def visible(cls):
        return cls.handler_alias is not None

    @classproperty
    def handler_name(cls):
        return cls.handler_alias.name if isinstance(cls.handler_alias, Enum) else cls.handler_alias

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

    properties = property(get_properties, set_properties)

    def _reload(self):
        """ Reload function on properties reset
        """
        pass

    def describe(self):
        return self.handler_alias, self.get_properties()

    @property
    def alias_and_properties(self):
        return {
            Keys.NAME: self.handler_alias,
            Keys.PROPERTIES: self.properties
        }

    @classproperty
    def handlers(cls) -> Dict[str, type]:
        """获取工具类名称到工具类的映射
        """
        attr_name = f'__handler_class_map_{cls.__name__}'
        if hasattr(PropertyHandlerMixin, attr_name):
            return getattr(PropertyHandlerMixin, attr_name)
        _handler_class_map = {}

        subclasses = TypeUtil.list_subclasses(cls)
        for subclass in subclasses:
            assert issubclass(subclass,
                              PropertyHandlerMixin), f'Class={subclass} not a subclass of PropertyHandlerMixin'
            if not hasattr(subclass, 'handler_alias') or subclass.handler_alias is None:
                logger.debug('Skip {} for no alias set', subclass)
                continue
            _handler_class_map[subclass.handler_name] = subclass

        setattr(cls, attr_name, _handler_class_map)
        return _handler_class_map

    @classproperty
    def handler_properties(cls) -> Dict[str, Dict[str, List[str]]]:
        """获取工具类名称到可以通过配置还原的工具类必需和可选属性的映射
        """
        attr_name = f'__handler_properties_map_{cls.__name__}'
        if hasattr(PropertyHandlerMixin, attr_name):
            return getattr(PropertyHandlerMixin, attr_name)
        _handler_properties_map = {}

        subclasses = TypeUtil.list_subclasses(cls)
        for subclass in subclasses:
            if not TypeUtil.is_subclass(subclass, PropertyHandlerMixin):
                continue
            if not hasattr(subclass, 'handler_alias') or subclass.handler_alias is None:
                logger.debug('Skip {} for no alias set', subclass)
                continue
            _handler_properties_map[subclass.handler_name] = {
                'required': subclass.required_properties,
                'optional': subclass.optional_properties
            }

        setattr(cls, attr_name, _handler_properties_map)
        return _handler_properties_map

    @classmethod
    def get_handler_by_name(cls, name: Union[str, Enum]) -> Type:
        if not name:
            raise ValueError('Handler name should be provided while querying handlers')
        if isinstance(name, Enum):
            name = name.name
        if name not in cls.handlers:
            raise ValueError(f'No handler configured for name={name} with class={cls.__name__}')
        return cls.handlers[name]


__all__ = [
    'SaveAndLoadConfigMixin',
    'PropertyHandlerMixin'
]
