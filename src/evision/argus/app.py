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
from typing import List, Union

from pydantic import BaseModel, Extra

from evision.lib.entity import ImageFrame
from evision.lib.log import logutil
from evision.lib.mixin import PropertyHandlerMixin
from evision.lib.parallel import ProcessWrapper
from evision.lib.util.types import ValueAsStrIntEnum
from evision.lib.video import BaseImageSource, ImageSourceConfig
from evision.lib.video import ImageSourceWrapperConfig
from evision.lib.video.wrapper import ImageSourceReader

logger = logutil.get_logger()


class App(ValueAsStrIntEnum):
    dummy = -42


class ArgusApplicationConfig(BaseModel):
    image_source_config: ImageSourceConfig = None
    source_wrapper_config: ImageSourceWrapperConfig = None
    app_handler: Union[App, str] = None
    frame_batch: int = 1
    fps: float = 24
    name: str = None
    paths: Union[str, list, None] = None
    answer_sigint: bool = False
    answer_sigterm: bool = False

    class Config():
        extra = Extra.allow
        arbitrary_types_allowed = True


class ArgusApp(ProcessWrapper, PropertyHandlerMixin):
    source: ImageSourceReader
    frame_batch: int

    # 是否必须配置数据源，在启动应用时检查
    __require_image_source__ = True

    @classmethod
    def construct(cls, config: ArgusApplicationConfig,
                  source: BaseImageSource = None,
                  wrapper: ImageSourceReader = None):
        if not source and not wrapper:
            raise ValueError('Image source not configured for argus application')
        if not wrapper:
            wrapper = ImageSourceReader(source, config.source_wrapper_config)
        app_class = cls.get_handler_by_name(config.app_handler) if config.app_handler is not None else cls
        return app_class(wrapper,
                         **config.dict(exclude={'image_source_config', 'source_wrapper_config', 'app_handler'}))

    def __init__(self, source_wrapper: ImageSourceReader,
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
        logger.debug("[{}] {} frames got", self.name, n_frames)
        if n_frames != 0:
            self.process_frame(image_frames)

    def process_frame(self, frames: Union[ImageFrame, List[ImageFrame]]):
        """Argus  应用处理图像帧方法
        """
        raise NotImplementedError

    def on_start(self):
        if self.__require_image_source__ and not self.source:
            raise ValueError(f'Failed starting app={self.name}, no image source provided')


ArgusApplication = ArgusApp


class DummyApplication(ArgusApp):
    handler_alias = App.dummy

    def process_frame(self, frames):
        logger.info(f'App[{self.name}] processing frame[{frames.frame_id} @ {time.time()}')
        pass
