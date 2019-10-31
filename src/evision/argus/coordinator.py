#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-30 14:26
# @version: 1.0
#
from collections import defaultdict
from threading import RLock
from typing import Dict, List, Union

from evision.argus.app import ArgusApplication, ArgusApplicationConfig
from evision.lib.log import logutil
from evision.lib.parallel import ProcessWrapper
from evision.lib.util import DictUtil
from evision.lib.video import (BaseImageSource, ImageSourceType, ImageSourceUtil, ImageSourceWrapper)
from evision.lib.video.source import ImageSourceConfig

logger = logutil.get_logger()


class ArgusCoordinator(ProcessWrapper):
    # (source_uri, source_type) 与 app 对应关系
    __dispatches: Dict[(Union[str, int], ImageSourceType), List[ArgusApplication]]
    # (source_uri, source_type) 与 image_source 对应关系
    __source_map: Dict[(Union[str, int], ImageSourceType), BaseImageSource]

    def __init__(self, *args, **kwargs):
        ProcessWrapper.__init__(self, *args, **kwargs)
        self.__dispatches = defaultdict(list)
        self.__source_map = dict()

        self.__lock = RLock()

    def add(self, app_config: ArgusApplicationConfig) -> ArgusApplication:
        image_source = self.register_source(app_config.image_source_config)
        source_wrapper = ImageSourceWrapper(image_source, app_config.source_wrapper_config)
        app = ArgusApplication.construct(app_config, wrapper=source_wrapper)

        with self.__lock:
            if not image_source.running:
                image_source.setDaemon(True)
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
                self.__source_map[source_key].stop()
                del self.__source_map[source_key]
                del self.__dispatches[source_key]

    def register_source(self, image_source_config: ImageSourceConfig) -> BaseImageSource:
        source_uri, source_type = ImageSourceUtil.parse_source_config(
            image_source_config.source_uri, image_source_config.source_type)
        source_key = (source_uri, source_type)
        with self.__lock:
            if not source_key in self.__source_map:
                source = BaseImageSource.construct(image_source_config)
                self.__source_map[source_key] = source
        return self.__source_map[source_key]

    def process(self):
        # 更新视频源
        with self.__lock:
            self.__dispatches = DictUtil.filter_values(self.__dispatches, ArgusApplication.is_alive)
            to_remove_sources = set(self.__source_map.keys) - set(self.__dispatches.keys())
            if not to_remove_sources:
                return
            for to_remove_source_config in to_remove_sources:
                source = self.__source_map[to_remove_source_config]
                assert isinstance(source, BaseImageSource)
                logger.info('Disconnecting to image source={}', source.info)
                source.stop()
                del self.__source_map[to_remove_source_config]

    def stop(self):
        super().stop()
        with self.__lock:
            for source_config, apps in self.__dispatches:
                for app in apps:
                    assert isinstance(app, ArgusApplication)
                    app.stop()
            for source in self.__source_map.values():
                source.stop()
