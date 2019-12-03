#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-11-29 13:48
# @version: 1.0
#
from enum import IntEnum


class TaskType(IntEnum):
    # 人脸检测
    FACE_DETECTION = 1
    # 人脸识别
    FACE_RECOGNITION = 2
    # 人脸属性
    FACE_PROPERTY = 3
    # 行人检测
    PEDESTRIAN_DETECTION = 4
    # 行人识别
    PEDESTRIAN_RECOGNITION = 5
    # 行人属性
    PEDESTRIAN_PROPERTY = 6
    # 动作识别
    ACTION_RECOGNITION = 7
    # 事件检测
    EVENT_DETECTION = 8
    # 追踪
    TRACKING = 9
    # 跨镜头追踪
    MULTI_TARGET_MULTI_CAMERA_TRACKING = 10
    # 活体检测
    LIVENESS_DETECTION = 11
    # 空
    DUMMY = -42


class GalleryType(IntEnum):
    FACE = 1
    PEDESTRIAN = 2
