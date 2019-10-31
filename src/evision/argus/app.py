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
from evision.lib.log import logutil

from evision.lib.parallel import ProcessWrapper
from evision.lib.video import ImageSourceWrapper

logger = logutil.get_logger()


class ArgusApplication(ProcessWrapper):
    source: ImageSourceWrapper
    frame_batch: int

    # 是否必须配置数据源，在启动应用时检查
    __require_image_source__ = True

    def __init__(self, source_wrapper: ImageSourceWrapper, frame_batch: int = 1,
                 name: str = None, paths: [str, list, None] = None,
                 answer_sigint: bool = False, answer_sigterm: bool = False, *args, **kwargs):
        self.source = source_wrapper
        self.frame_batch = frame_batch

        super().__init__(name, paths, answer_sigint, answer_sigterm, *args, **kwargs)

    @property
    def source_id(self):
        return None if not self.source else self.source.source_id

    def process(self):
        """应用通过重载本方法实现功能"""
        image_frames = self.source.provide(self.frame_batch)
        if not image_frames:
            return
        logger.info("{} frames got", len(image_frames))
        self.process_frame(image_frames)

    def process_frame(self, image_frames):
        """Argus  应用处理图像帧方法，各应用必须实现"""
        raise NotImplementedError

    def is_inited(self):
        if not self.is_alive():
            return False
        return True if not self.source else self.source.is_alive() and self.is_alive()

    def on_start(self):
        if self.__require_image_source__ and not self.source:
            raise ValueError(f'Failed to start app={self.name}, no image source provided')
