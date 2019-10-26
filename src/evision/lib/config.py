# -*- coding: utf-8 -*-
#
# Copyright 2018 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-07-27 17:09
# @version: 1.0
#
"""配置文件读写"""

import ast
import threading
from configparser import ConfigParser
from os import path as osp

from evision.lib.decorator import Singleton

__all__ = [
    'ConfigSection',
    'EvisionConfig'
]


class ConfigSection(object):
    """主要配置section"""
    TORNADO = 'tornado'
    PROJECT = 'project'
    PATRONUM = 'patronum'
    VIDEO = 'video'
    PROCESSOR = 'processor'
    DETECTION = 'detection'
    THRESHOLD = 'threshold'
    SYNC = 'sync'

    @staticmethod
    def get_section_name(section, type_):
        if not type_:
            return section
        return '{}_{}'.format(type_, section)


class EvisionConfig(object):
    """ini配置读写封装"""
    __metaclass__ = Singleton

    def __init__(self, default_config=None):
        self.__cfg = ConfigParser()
        self.__lock = threading.Lock()
        self.__last_config_file = None
        self.__default_config = default_config
        self.load_default()

    def load(self, config_file):
        self.__last_config_file = config_file
        self.__cfg.read(config_file, encoding='utf-8')

    def load_default(self):
        """读取默认配置"""
        if self.__default_config and osp.isfile(self.__default_config):
            self.load(self.__default_config)

    def get(self, *value):
        if len(value) == 1:
            value = value[0]
            if '.' in value:
                return self.__cfg.get(*value.split('.'))
            # value is a section
            return self.__cfg.items(value)

        return self.__cfg.get(*value, fallback=None)

    def getliteral(self, section, option, default_=None):
        if section is None or option is None:
            raise ValueError('Section and option should both be provided')
        if not self.__cfg.has_option(section, option):
            return None
        value = self.__cfg.get(section, option, raw=True)
        if not value:
            return default_
        try:
            return ast.literal_eval(value)
        except ValueError:
            return default_

    def getlist(self, section, option):
        return self.getliteral(section, option, default_=[])

    def append_to_list(self, section, option, value, save=False):
        current_list = self.getlist(section, option)
        if not current_list:
            current_list = []
        current_list.append(value)
        self.__cfg.set(section, option, str(current_list))
        if save:
            self.save()

    def remove_from_list(self, section, option, value, save=False):
        current_list = self.getlist(section, option)
        if not current_list or value not in list:
            return
        current_list.remove(value)
        self.__cfg.set(section, option, str(current_list))
        if save:
            self.save()

    def getdict(self, section, option):
        return self.getliteral(section, option, default_={})

    def update_to_dict(self, section, option, key, value, save=False):
        current_dict = self.getdict(section, option)
        if not current_dict:
            current_dict = {}
        current_dict.update({
            key: value
        })
        self.set(section, option, str(current_dict))
        if save:
            self.save()

    def remove_from_dict(self, section, option, key, save=False):
        current_dict = self.getdict(section, option)
        if not current_dict or key not in current_dict:
            return
        del current_dict[key]
        self.__cfg.set(section, option, str(current_dict))
        if save:
            self.save()

    def getset(self, section, option):
        return self.getliteral(section, option, default_=set())

    def add_to_set(self, section, option, value, save=False):
        current_set = self.getset(section, option)
        if not current_set:
            current_set = set()
        current_set.add(value)
        self.__cfg.set(section, option, str(current_set))
        if save:
            self.save()

    def remove_from_set(self, section, option, value, save=False):
        current_set = self.getset(section, option)
        if not current_set or value not in current_set:
            return
        current_set.remove(value)
        self.__cfg.set(section, option, str(current_set))
        if save:
            self.save()

    def update_section(self, section, configs, save=False):
        if not self.__cfg.has_section(section):
            self.__cfg.add_section(section)
        for k, v in configs.items():
            if v is None:
                continue
            self.__cfg.set(section, k, str(v))
        if save:
            self.save()

    def replace_section(self, section, configs, save=False):
        if self.__cfg.has_section(section):
            self.__cfg.remove_section(section)
        self.update_section(section, configs, save=save)

    def load_last(self):
        if not osp.isfile(self.__default_config):
            return False
        last_cfg = ConfigParser()
        last_cfg.read(self.__default_config, encoding='utf-8')
        self.load(self.__default_config)
        return True

    def load_config(self, config_file=None):
        if not config_file:
            return

        self.load_default()
        if osp.exists(config_file):
            self.load(config_file)
        self.save()

    def save(self):
        with self.__lock:
            self.__cfg.write(open(self.__default_config, 'w'))

    def __getattr__(self, name):
        """将当前类作为ConfigParser对象的代理"""
        return getattr(self.__cfg, name)

    def __str__(self):
        __output = '=' * 80 + '\n'
        for section in self.sections():
            __output += '[{}]'.format(section) + '\n'
            for key, value in self.items(section):
                __output += '\t{} = {}'.format(key, value) + '\n'
        __output += '-' * 80 + '\n'
        return __output

    def print_configurations(self):
        print(self)
