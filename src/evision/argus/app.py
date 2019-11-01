#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# Argus general application with image source processing
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-30 14:26
# @version: 1.0
#
import time
from enum import IntEnum
from typing import List, Union

from pydantic import BaseModel

from evision.lib.entity import ImageFrame
from evision.lib.log import logutil
from evision.lib.mixin import PropertyHandlerMixin
from evision.lib.parallel import ProcessWrapper
from evision.lib.video import BaseImageSource, ImageSourceConfig
from evision.lib.video import ImageSourceWrapper, ImageSourceWrapperConfig

logger = logutil.get_logger()


class App(IntEnum):
    dummy = -42


class ArgusApplicationConfig(BaseModel):
    image_source_config: ImageSourceConfig = None
    source_wrapper_config: ImageSourceWrapperConfig = None
    frame_batch: int = 1
    fps: float = 24
    name: str = None
    paths: Union[str, list, None] = None
    extra: dict = {}

    class Config:
        arbitrary_types_allowed = True


class ArgusApp(ProcessWrapper, PropertyHandlerMixin):
    source: ImageSourceWrapper
    frame_batch: int

    # 是否必须配置数据源，在启动应用时检查
    __require_image_source__ = True

    @classmethod
    def construct(cls, config: ArgusApplicationConfig,
                  source: BaseImageSource = None,
                  wrapper: ImageSourceWrapper = None):
        if not source and not wrapper:
            raise ValueError('Image source not configured for argus application')
        if not wrapper:
            wrapper = ImageSourceWrapper(source, config.source_wrapper_config)
        return cls(wrapper, config.frame_batch, config.fps,
                   config.name, config.paths, **config.extra)

    def __init__(self, source_wrapper: ImageSourceWrapper,
                 frame_batch: int = 1, fps: float = 24,
                 name: str = None, paths: Union[str, list, None] = None,
                 answer_sigint: bool = False, answer_sigterm: bool = False, *args, **kwargs):
        self.source = source_wrapper
        self.frame_batch = frame_batch
        self.fps = fps

        super().__init__(name, paths, answer_sigint, answer_sigterm,
                         interval=1.0 / self.fps if self.fps != 0 else None,
                         *args, **kwargs)

    def process(self):
        """应用通过重载本方法实现功能"""
        image_frames = self.source.provide(self.frame_batch)
        n_frames = int(image_frames is not None) if self.frame_batch == 1 else len(image_frames)
        logger.debug("{} frames got", n_frames)
        if n_frames != 0:
            self.process_frame(image_frames)

    def process_frame(self, frames: Union[ImageFrame, List[ImageFrame]]):
        """Argus  应用处理图像帧方法
        """
        raise NotImplementedError

    def init(self):
        super().init()
        logger.debug('Application={} initializing...', self.name)
        if self.source and not self.source.is_alive():
            logger.debug('Opening image source: {}', self.source)
            self.source.open_image_source()

    def is_inited(self):
        return True if not self.source else self.source.is_alive()

    def on_start(self):
        if self.__require_image_source__ and not self.source:
            raise ValueError(f'Failed starting app={self.name}, no image source provided')
        if not self.source.is_alive():
            raise ValueError(f'Failed starting app={self.name}, image source not opened')

    @classmethod
    def app_class(cls, name: App):
        return cls.get_handler_by_name(name.name)


ArgusApplication = ArgusApp


class DummyApplication(ArgusApp):
    handler_alias = App.dummy

    def process_frame(self, frames):
        logger.info(f'{self.name} @ {time.time()}')
        pass
