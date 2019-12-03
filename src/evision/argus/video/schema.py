#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-12-03 09:14
# @version: 1.0
#
from typing import Union

from pydantic import BaseModel, Extra, validator

from evision.lib.entity import Shape, Zone
from evision.argus.video import ImageSourceType, ImageSourceUtil
from evision.argus.constants.resource import ImageSourceHandler


class ImageSourceConfig(BaseModel):
    source_id: str = None
    source_uri: Union[str, int]
    source_type: Union[ImageSourceType, int]
    handler_name: Union[ImageSourceHandler, str] = ImageSourceHandler.VIDEO_CAPTURE
    frame_size: Shape = None
    width: int = None  # deprecated
    height: int = None  # deprecated
    fps: float = 24
    frame_queue_size: int = 24
    name: str = None
    description: str = None

    class Config:
        extra = Extra.allow
        arbitrary_types_allowed = True


class ImageSourceReaderConfig(ImageSourceConfig):
    source_id: str
    process_rate: int = None
    zoom: Shape = None
    zone: Zone = None

    @validator('zoom')
    def validate_zoom(cls, v):
        if v is None:
            return None
        assert ImageSourceUtil.check_frame_shape(v.width, v.height)
        return v

    @validator('zone')
    def validate_zone(cls, v, values):
        """ 校验视频源区域配置
        """
        if v is None:
            return v
        assert isinstance(v, Zone)
        zoomed_shape = values['zoom'] if 'zoom' in values else None
        if zoomed_shape is None:
            return
        assert isinstance(zoomed_shape, Shape), 'Invalid Shape'
        v.validate_shape(zoomed_shape.width, zoomed_shape.height)

        return v
