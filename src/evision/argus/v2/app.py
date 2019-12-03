#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-12-02 15:47
# @version: 1.0
#

import time
from typing import Dict, List, Union

from pydantic import BaseModel, Extra, validator

from evision.argus.constants.task import TaskType
from evision.argus.video import ImageSourceReader
from evision.argus.video import ImageSourceReaderConfig
from evision.lib.entity import ImageFrame
from evision.lib.log import logutil
from evision.lib.mixin import PropertyHandlerMixin
from evision.lib.parallel import ProcessWrapper

logger = logutil.get_logger()


class BaseArgusAppConfig(BaseModel):
    # 应用类型
    app_type: TaskType = TaskType.DUMMY
    # 应用名称
    app_name: str = None
    # 应用关联视频源封装
    source_wrapper_config: Dict[str, ImageSourceReaderConfig]
    # 应用关联视频源 ID 列表
    source_ids: List[str]
    # 应用关联群组列表
    group_ids: List[str]
    # 每次处理图像帧数
    frame_batch: int = 1
    # 处理帧率
    frame_rate: float = 24
    # 应用备注
    remark: str = None

    class Config:
        extra = Extra.allow
        arbitrary_types_allowed = True

    @validator('source_ids')
    def ensure_source_configs(cls, v, values):
        if not v:
            raise ValueError('No image sources provided')
        assert 'source_wrapper_config' in values, \
            f'No image source configuration provided for source_ids={v}'
        assert isinstance(v, list)
        source_ids_unconfigured = set(v) - set(values['source_wrapper_config'].keys())
        assert not source_ids_unconfigured, \
            f'Image source unconfigured: {source_ids_unconfigured}'
        return v


class ArgusAppConfig(BaseArgusAppConfig):
    app_id: str
    app_type: TaskType
    name: str


class BaseArgusApp(ProcessWrapper, PropertyHandlerMixin):
    # 是否必须配置数据源，在启动应用时检查
    REQUIRE_IMAGE_SOURCE = True

    @classmethod
    def construct(cls, config: BaseArgusAppConfig, *args, **kwargs):
        app_class = cls.get_handler_by_name(config.app_type)
        assert issubclass(app_class, BaseArgusApp)
        return app_class(config, *args, **kwargs)

    @staticmethod
    def get_source_configs(source_ids: List[str],
                           source_configs: Dict[str, ImageSourceReaderConfig]):
        return [source_configs[source_id] for source_id in source_ids]

    def __init__(self, config: BaseArgusAppConfig,
                 paths: Union[str, list, None] = None,
                 answer_sigint: bool = False, answer_sigterm: bool = False,
                 *args, **kwargs):
        self._app_config = config
        self.interval = 1.0 / config.frame_rate if config.frame_rate else None
        self.source_configs = BaseArgusApp.get_source_configs(
            config.source_ids, config.source_wrapper_config)
        self.sources = [ImageSourceReader(config) for config in self.source_configs]
        super().__init__(config.app_name, paths, answer_sigint, answer_sigterm,
                         interval=self.interval, *args, **kwargs)

    def process(self):
        """应用通过重载本方法实现功能"""
        for source_reader in self.sources:
            image_frames = source_reader.provide(self._app_config.frame_batch)
            n_frames = int(image_frames is not None) if self._app_config.frame_batch == 1 else len(image_frames)
            logger.debug("[{}] {} frames got", self.name, n_frames)
            if n_frames != 0:
                self.process_frame(image_frames)

    def process_frame(self, frames: Union[ImageFrame, List[ImageFrame]]):
        """Argus  应用处理图像帧方法
        """
        raise NotImplementedError

    def on_start(self):
        if self.REQUIRE_IMAGE_SOURCE and not self.sources:
            raise ValueError(f'Failed starting app={self.name}, no image source provided')


class DummyApp(BaseArgusApp):
    handler_alias = TaskType.DUMMY

    def process_frame(self, frames):
        logger.info(f'App[{self.name}] processing frame[{frames.frame_id} @ {time.time()}')
        pass
