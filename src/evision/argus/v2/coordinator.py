#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-30 14:26
# @version: 1.0
#
import itertools
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple, Type, Union

from evision.argus.constants.resource import ImageSourceType
from evision.argus.v2.app import BaseArgusApp, BaseArgusAppConfig
from evision.argus.video import BaseImageSource, ImageSourceConfig
from evision.lib.log import logutil
from evision.lib.parallel import ProcessWrapper
from evision.lib.util import DictUtil

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
        if clazz:
            image_source_config.handler_name = clazz.handler_name
        with self.__lock:
            if image_source_config.source_key not in self.__source_map:
                source = BaseImageSource.construct(image_source_config)
                source.daemon = True
                source.start()
                self.__source_map[image_source_config.source_key] = source
        return self.__source_map[image_source_config.source_key]

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
    __dispatches: Dict[Tuple[Union[str, int], ImageSourceType], List[BaseArgusApp]]

    def __init__(self, *args, **kwargs):
        ProcessWrapper.__init__(self, *args, **kwargs)
        self.__dispatches = defaultdict(list)
        self.__source_coordinator = DictImageSourceCoordinator()

        self.__lock = Lock()

    def add(self, app_config: BaseArgusAppConfig,
            app_clazz: Type[BaseArgusApp] = None) -> BaseArgusApp:
        if app_clazz:
            app_config.app_handler = app_clazz.handler_alias
        app = BaseArgusApp.construct(app_config)
        for source_config in app.source_configs:
            self.__source_coordinator.register(source_config)

        with self.__lock:
            # APP 的执行不依赖图像源状态
            app.daemon = True
            app.start()

            for config in app.source_configs:
                self.__dispatches[config.source_key].append(app)
        return app

    def remove(self, app: BaseArgusApp):
        app.stop()
        with self.__lock:
            for source_config in app.source_configs:
                self.__dispatches[source_config.source_key].remove(app)
                if not self.__dispatches[source_config.source_key]:
                    self.__source_coordinator.remove(source_config.source_key)
                    del self.__dispatches[source_config.source_key]

    def process(self):
        # 更新视频源
        with self.__lock:
            self.__dispatches = DictUtil.filter_values(self.__dispatches, BaseArgusApp.is_alive)
            to_remove_sources = set(self.__source_coordinator.source_keys) - set(self.__dispatches.keys())
            if not to_remove_sources:
                return
            for source_key in to_remove_sources:
                self.__source_coordinator.remove(source_key)
        time.sleep(10)

    def stop(self):
        super().stop()
        with self.__lock:
            for app in self.apps:
                assert isinstance(app, BaseArgusApp)
                app.stop()
            self.__source_coordinator.remove_all()

    @property
    def n_image_sources(self):
        return len(self.__source_coordinator.source_keys)

    @property
    def apps(self):
        return set(itertools.chain(*self.__dispatches.values()))

    @property
    def n_apps(self):
        return len(self.apps)


__all__ = [
    'ImageSourceCoordinator',
    'DictImageSourceCoordinator',
    'ArgusCoordinator'
]
