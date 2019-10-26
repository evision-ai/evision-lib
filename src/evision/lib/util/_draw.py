#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-25 18:13
# @version: 1.0
#
import cv2

from evision.lib.entity import Vertex, Zone

__all__ = [
    'DrawUtil'
]


class DrawUtil(object):
    """OpenCV 图像处理接口封装"""

    @staticmethod
    def put_text(image, text, org=None, color=None, line_type=None):
        """在图像上添加文字"""
        if not color:
            color = (0, 255, 0)
        if not line_type:
            line_type = 1
        if not org:
            org = (5, image.shape[0] - 5)
        elif isinstance(org, Vertex):
            org = org.to_tuple()
        cv2.putText(image, text, org,
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.5, color=color, lineType=line_type)

    @staticmethod
    def draw_rectangle(image, start, end, color=None, line_type=None):
        """在图像上添加矩形"""
        if not color:
            color = (0, 255, 0)
        if not line_type:
            line_type = 1
        if isinstance(start, Vertex):
            start = start.to_tuple()
        if isinstance(end, Vertex):
            start = end.to_tuple()
        cv2.rectangle(image, start, end, color, line_type)

    @staticmethod
    def draw_zone(image, zone: Zone, bias=None):
        """使用SamaritanZone在图像上添加举行"""
        if not zone:
            return
        if not bias:
            start_point = zone.start_point
            end_point = zone.end_point
        else:
            start_point = zone.start_point + bias
            end_point = zone.end_point + bias
        DrawUtil.draw_rectangle(image, start_point.to_tuple(), end_point.to_tuple())
