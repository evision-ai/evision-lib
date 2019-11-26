#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-30 14:26
# @version: 1.0
#
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple, Type, Union

from evision.argus.app import ArgusApp, ArgusApplication, ArgusApplicationConfig
from evision.lib.log import logutil
from evision.lib.parallel import ProcessWrapper
from evision.lib.util import DictUtil
from evision.lib.video import BaseImageSource, ImageSourceConfig
from evision.lib.video import ImageSourceType, ImageSourceUtil
from evision.lib.video.wrapper import ImageSourceReader

logger = logutil.get_logger()


class ImageSourceCoordinator(object):
    """图像源调度

    预留接口定义，目前仅实现内存 Dict 信息保存方式，可以扩展为外部存储，如 Redis、DB
    """

    def register(self, image_source_config: ImageSourceConfig) -> BaseImageSource:
        raise NotImplementedError

    def remove(self, source_key: Tuple[str or int, ImageSourceType]):
        raise NotImplementedError

    def remove_all(self):
        keys = list(self.source_keys)
        for source_key in keys:
            self.remove(source_key)

    @property
    def source_keys(self):
        raise NotImplementedError


class DictImageSourceCoordinator(ImageSourceCoordinator):
    # (source_uri, source_type) 与 image_source 对应关系
    __source_map: Dict[Tuple[str or int, ImageSourceType], BaseImageSource]

    def __init__(self):
        self.__source_map = dict()
        self.__lock = Lock()

    def register(self, image_source_config: ImageSourceConfig,
                 clazz: Type[BaseImageSource] = None) -> BaseImageSource:
        source_uri, source_type = ImageSourceUtil.parse_source_config(
            image_source_config.source_uri, image_source_config.source_type)
        source_key = (source_uri, source_type)
        if clazz:
            image_source_config.handler_name = clazz.handler_name
        with self.__lock:
            if source_key not in self.__source_map:
                source = BaseImageSource.construct(image_source_config)
                self.__source_map[source_key] = source
        return self.__source_map[source_key]

    def remove(self, source_key: (Union[str, int], ImageSourceType)):
        with self.__lock:
            if source_key not in self.__source_map:
                return
            source = self.__source_map.pop(source_key)
            logger.info('Disconnecting to image source={}', source.info)
            source.stop()

    @property
    def source_keys(self):
        with self.__lock:
            return self.__source_map.keys()


class ArgusCoordinator(ProcessWrapper):
    # (source_uri, source_type) 与 app 对应关系
    __dispatches: Dict[Tuple[Union[str, int], ImageSourceType], List[ArgusApplication]]

    def __init__(self, *args, **kwargs):
        ProcessWrapper.__init__(self, *args, **kwargs)
        self.__dispatches = defaultdict(list)
        self.__source_coordinator = DictImageSourceCoordinator()

        self.__lock = Lock()

    def add(self, app_config: ArgusApplicationConfig,
            app_type: Type[ArgusApp] = None,
            source_type: Type[BaseImageSource] = None) -> ArgusApplication:
        image_source = self.__source_coordinator.register(app_config.image_source_config, source_type)
        source_wrapper = ImageSourceReader(image_source, app_config.source_wrapper_config)
        if app_type:
            app_config.app_handler = app_type.handler_alias
        app = ArgusApp.construct(app_config, wrapper=source_wrapper)

        with self.__lock:
            if not image_source.running:
                with image_source.read_lock:
                    if not image_source.running:
                        image_source.daemon = True
                        image_source.start()
            app.daemon = True
            app.start()
            self.__dispatches[image_source.uri_and_type].append(app)
        return app

    def remove(self, argus_app: ArgusApplication):
        source_key = argus_app.source.uri_and_type
        argus_app.stop()
        with self.__lock:
            self.__dispatches[source_key].remove(argus_app)
            if not self.__dispatches[source_key]:
                self.__source_coordinator.remove(source_key)
                del self.__dispatches[source_key]

    def process(self):
        # 更新视频源
        with self.__lock:
            self.__dispatches = DictUtil.filter_values(self.__dispatches, ArgusApplication.is_alive)
            to_remove_sources = set(self.__source_coordinator.source_keys) - set(self.__dispatches.keys())
            if not to_remove_sources:
                return
            for source_key in to_remove_sources:
                self.__source_coordinator.remove(source_key)
        time.sleep(10)

    def stop(self):
        super().stop()
        with self.__lock:
            for source_config, apps in self.__dispatches.items():
                for app in apps:
                    assert isinstance(app, ArgusApplication)
                    app.stop()
            self.__source_coordinator.remove_all()

    @property
    def n_image_sources(self):
        return len(self.__source_coordinator.source_keys)

    @property
    def n_apps(self):
        return sum(len(v) for v in self.__dispatches.values())


__all__ = [
    'ImageSourceCoordinator',
    'DictImageSourceCoordinator',
    'ArgusCoordinator'
]
