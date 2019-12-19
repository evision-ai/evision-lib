# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-11-01 17:19
# @version: 1.0
#
import enum

import pytest

from evision.lib.constant import Keys
from evision.lib.error import PropertiesNotProvided
from evision.lib.log import logutil
from evision.lib.mixin import PropertyHandlerMixin

logger = logutil.get_logger()


class _BaseClass(PropertyHandlerMixin):
    def __init__(self, **data):
        for k, v in data.items():
            setattr(self, k, v)


class _SubClassA(_BaseClass):
    required_properties = ['foo', 'bar']
    handler_alias = 'class-a'


class _SubClassB(_BaseClass):
    optional_properties = ['FOO', 'BAR']
    handler_alias = 'class-b'


class _SubClassC(_SubClassA):
    required_properties = ['foobar']
    optional_properties = ['FOOBAR']
    handler_alias = 'class-c'


class ClassName(enum.Enum):
    class_d = 1
    class_e = 'str'


class _ClassD(PropertyHandlerMixin):
    handler_alias = ClassName.class_d


class _ClassE(_ClassD):
    handler_alias = ClassName.class_e


class TestPropertyHandlerMixin(object):
    def test_check_property_map(self):
        PropertyHandlerMixin.check_property_map({})
        PropertyHandlerMixin.check_property_map({'foo': None}, 'foo')

        with pytest.raises(PropertiesNotProvided) as e:
            PropertyHandlerMixin.check_property_map({}, 'foo')
            assert isinstance(e, ValueError)

    def test_visible(self):
        assert not _BaseClass.visible
        assert _SubClassA.visible
        assert _SubClassB.visible
        assert _SubClassC.visible

    def handler_name(self):
        assert _BaseClass.handler_name is None
        assert _SubClassA.handler_name == 'class-a'
        assert _SubClassB.handler_name == 'class-b'
        assert _SubClassC.handler_name == 'class-c'
        assert _ClassD.handler_name == 'class_d'
        assert _ClassE.handler_name == 'class_e'

    def test_get_properties(self):
        keys = ['foo', 'bar', 'FOO', 'BAR', 'a', 'b']
        properties = {k: k for k in keys}

        a = _SubClassA(**properties)
        properties_a = a.properties
        assert len(properties_a) == len(_SubClassA.required_properties)
        for key in _SubClassA.required_properties:
            assert key in properties_a and properties_a[key] == key
        assert 'FOO' not in properties_a

        b = _SubClassB(**properties)
        properties_b = b.properties
        assert len(properties_b) == len(_SubClassB.optional_properties)
        for key in _SubClassB.optional_properties:
            assert key in properties_b and properties_b[key] == key
        assert 'foo' not in properties_b

    def test_describe(self):
        keys = ['foo', 'bar', 'FOO', 'BAR', 'a', 'b']
        properties = {k: k for k in keys}

        handler_alias, properties = _SubClassA(**properties).describe()
        assert handler_alias == _SubClassA.handler_alias
        assert len(properties) == len(_SubClassA.required_properties)
        for key in _SubClassA.required_properties:
            assert key in properties and properties[key] == key
        assert 'FOO' not in properties

    def test_alias_and_properties(self):
        keys = ['foo', 'bar', 'FOO', 'BAR', 'a', 'b']
        properties = {k: k for k in keys}

        alias_properties = _SubClassA(**properties).alias_and_properties
        assert isinstance(alias_properties, dict)
        assert Keys.NAME in alias_properties and Keys.PROPERTIES in alias_properties
        handler_alias, properties = alias_properties[Keys.NAME], alias_properties[Keys.PROPERTIES]
        assert handler_alias == _SubClassA.handler_alias
        assert len(properties) == len(_SubClassA.required_properties)
        for key in _SubClassA.required_properties:
            assert key in properties and properties[key] == key
        assert 'FOO' not in properties

    def test_handlers(self):
        handlers = _BaseClass.handlers
        assert len(handlers) == 3
        assert 'class-a' in handlers and handlers['class-a'] == _SubClassA
        assert 'class-b' in handlers and handlers['class-b'] == _SubClassB
        assert 'class-c' in handlers and handlers['class-c'] == _SubClassC

        assert _SubClassA.handlers == {
            'class-a': _SubClassA,
            'class-c': _SubClassC
        }
        assert len(_SubClassA.handlers) == 2
        assert len(_SubClassB.handlers) == 1
        assert len(_SubClassC.handlers) == 1

        assert len(_ClassD.handlers) == 2
        assert len(_ClassE.handlers) == 1

    def test_handler_properties(self):
        handlers_properties = _BaseClass.handler_properties
        assert len(handlers_properties) == 3
        assert 'class-a' in handlers_properties
        assert 'class-b' in handlers_properties
        assert 'class-c' in handlers_properties

    def test_get_handler_by_name(self):
        assert _BaseClass.get_handler_by_name('class-a') == _SubClassA
        assert _BaseClass.get_handler_by_name('class-b') == _SubClassB
        assert _BaseClass.get_handler_by_name('class-c') == _SubClassC
