# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2019-11-01 17:19
# @version: 1.0
#

import pytest

from evision.lib.constant import Keys
from evision.lib.error import PropertiesNotProvided
from evision.lib.log import logutil
from evision.lib.mixin import PropertyHandlerMixin

logger = logutil.get_logger()


class BaseClass(PropertyHandlerMixin):
    def __init__(self, **data):
        for k, v in data.items():
            setattr(self, k, v)


class SubClassA(BaseClass):
    required_properties = ['foo', 'bar']
    handler_alias = 'class-a'


class SubClassB(BaseClass):
    optional_properties = ['FOO', 'BAR']
    handler_alias = 'class-b'


class SubClassC(SubClassA):
    required_properties = ['foobar']
    optional_properties = ['FOOBAR']
    handler_alias = 'class-c'


class TestPropertyHandlerMixin(object):
    def test_check_property_map(self):
        PropertyHandlerMixin.check_property_map({})
        PropertyHandlerMixin.check_property_map({'foo': None}, 'foo')

        with pytest.raises(PropertiesNotProvided) as e:
            PropertyHandlerMixin.check_property_map({}, 'foo')
            assert isinstance(e, ValueError)

    def test_visible(self):
        assert not BaseClass.visible()
        assert SubClassA.visible()
        assert SubClassB.visible()
        assert SubClassC.visible()

    def test_get_properties(self):
        keys = ['foo', 'bar', 'FOO', 'BAR', 'a', 'b']
        properties = {k: k for k in keys}

        a = SubClassA(**properties)
        properties_a = a.properties
        assert len(properties_a) == len(SubClassA.required_properties)
        for key in SubClassA.required_properties:
            assert key in properties_a and properties_a[key] == key
        assert 'FOO' not in properties_a

        b = SubClassB(**properties)
        properties_b = b.properties
        assert len(properties_b) == len(SubClassB.optional_properties)
        for key in SubClassB.optional_properties:
            assert key in properties_b and properties_b[key] == key
        assert 'foo' not in properties_b

    def test_describe(self):
        keys = ['foo', 'bar', 'FOO', 'BAR', 'a', 'b']
        properties = {k: k for k in keys}

        handler_alias, properties = SubClassA(**properties).describe()
        assert handler_alias == SubClassA.handler_alias
        assert len(properties) == len(SubClassA.required_properties)
        for key in SubClassA.required_properties:
            assert key in properties and properties[key] == key
        assert 'FOO' not in properties

    def test_alias_and_properties(self):
        keys = ['foo', 'bar', 'FOO', 'BAR', 'a', 'b']
        properties = {k: k for k in keys}

        alias_properties = SubClassA(**properties).alias_and_properties
        assert isinstance(alias_properties, dict)
        assert Keys.NAME in alias_properties and Keys.PROPERTIES in alias_properties
        handler_alias, properties = alias_properties[Keys.NAME], alias_properties[Keys.PROPERTIES]
        assert handler_alias == SubClassA.handler_alias
        assert len(properties) == len(SubClassA.required_properties)
        for key in SubClassA.required_properties:
            assert key in properties and properties[key] == key
        assert 'FOO' not in properties

    def test_handlers(self):
        handlers = BaseClass.handlers()
        assert len(handlers) == 3
        assert 'class-a' in handlers and handlers['class-a'] == SubClassA
        assert 'class-b' in handlers and handlers['class-b'] == SubClassB
        assert 'class-c' in handlers and handlers['class-c'] == SubClassC

        assert SubClassA.handlers() == {
            'class-a': SubClassA,
            'class-c': SubClassC
        }
        assert len(SubClassA.handlers()) == 2
        assert len(SubClassB.handlers()) == 1
        assert len(SubClassC.handlers()) == 1

    def test_handler_properties(self):
        handlers_properties = BaseClass.handler_properties()
        assert len(handlers_properties) == 3
        assert 'class-a' in handlers_properties
        assert 'class-b' in handlers_properties
        assert 'class-c' in handlers_properties

    def test_get_handler_by_name(self):
        assert BaseClass.get_handler_by_name('class-a') == SubClassA
        assert BaseClass.get_handler_by_name('class-b') == SubClassB
        assert BaseClass.get_handler_by_name('class-c') == SubClassC
