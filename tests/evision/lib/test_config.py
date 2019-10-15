# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-07-27 19:04
# @version: 1.0
#
from os import path as osp

from evision.lib.config import ConfigSection, EvisionConfig

__config_file__ = osp.join(osp.dirname(osp.abspath(__file__)), 'test-config.ini')
CONFIG = EvisionConfig()
CONFIG.load(__config_file__)


def test_config_loading():
    assert CONFIG.has_section(ConfigSection.PROJECT)


def test_get_config():
    assert CONFIG.get('project.profile') == 'test'
    assert CONFIG.get('project', 'profile') == 'test'
    assert len(CONFIG.get('project')) == 4
    assert 'log_dir' in CONFIG.options('project')


def test_get_literal():
    names = CONFIG.getlist('video', 'names')
    assert len(names) == 1
    assert 'usb_camera' in names
    names = CONFIG.getlist('video', 'name1')
    assert names is None
    name_set = CONFIG.getset('video', 'name_set')
    assert len(name_set) == 2
    assert 1 in name_set and 2 in name_set
    name_dict = CONFIG.getdict('video', 'name_dict')
    assert len(name_dict) == 2
    assert 1 in name_dict and 2 in name_dict
    assert type(name_dict) is dict
    value = CONFIG.getliteral('video', 'none')
    assert value is None
    fps = CONFIG.getliteral('video', 'fps')
    assert fps == 300


def test_write():
    assert CONFIG.getint('video', 'fps') == 300
    CONFIG.set('video', 'fps', '5')
    CONFIG.write(open(__config_file__, 'w'))
    assert CONFIG.getint('video', 'fps') == 5
    CONFIG.set('video', 'fps', '300')
    CONFIG.write(open(__config_file__, 'w'))
    assert CONFIG.getint('video', 'fps') == 300


def test_update():
    another_name = 'another_name'

    CONFIG.append_to_list('video', 'names', another_name)
    names = CONFIG.getlist('video', 'names')
    assert len(names) == 2
    assert another_name in names

    CONFIG.append_to_list('video', 'names1', another_name)
    names = CONFIG.getlist('video', 'names1')
    assert len(names) == 1
    assert another_name in names

    CONFIG.add_to_set('video', 'name_set', another_name)
    names = CONFIG.getset('video', 'name_set')
    assert len(names) == 3
    assert another_name in names

    CONFIG.add_to_set('video', 'name_set1', another_name)
    names = CONFIG.getset('video', 'name_set1')
    assert len(names) == 1
    assert another_name in names

    CONFIG.update_to_dict('video', 'name_dict', another_name, 2)
    name_dict = CONFIG.getdict('video', 'name_dict')
    assert len(name_dict) == 3
    assert another_name in name_dict and name_dict[another_name] == 2

    CONFIG.update_to_dict('video', 'name_dict', another_name, 3)
    name_dict = CONFIG.getdict('video', 'name_dict')
    assert len(name_dict) == 3
    assert another_name in name_dict and name_dict[another_name] == 3
