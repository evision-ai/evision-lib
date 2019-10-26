# -*- coding: utf-8 -*-
# 图像描述数据结构封装
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-06-07 14:46
# @version: 1.0

import collections
import time

import cv2
import numpy as np

from evision.lib import decorator

__all__ = [
    'Vertex', 'Vector',
    'Zone',
    'ImageFrame',
    'Detection'
]


class Vertex(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_list(self):
        return [self.x, self.y]

    def to_tuple(self):
        return self.x, self.y

    def times(self, times):
        return self.__class__(self.x * times, self.y * times)

    @classmethod
    def _parse(cls, value):
        if value is None:
            return None
        elif isinstance(value, Vertex):
            return value
        elif isinstance(value, collections.abc.Sequence):
            return Vertex(value[0], value[1])
        return None

    def __str__(self):
        return '({}, {})'.format(self.x, self.y)

    def __eq__(self, other):
        other = Vertex._parse(other)
        if not other:
            return False
        return self.x == other.x and self.y == other.y

    def __len__(self):
        """collections.Sized"""
        return 0 if self.x is None or self.y is None else 2

    def __iter__(self):
        """collections.Iterable"""
        return iter(self.to_list())

    def __add__(self, other):
        other = Vertex._parse(other)
        if not other:
            raise ValueError(f'Invalid vertex: {other}')
        return Vertex(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        other = Vertex._parse(other)
        if not other:
            raise ValueError(f'Invalid vertex: {other}')
        return Vertex(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        other = Vertex._parse(other)
        if not other:
            raise ValueError(f'Invalid vertex: {other}')
        return Vertex(self.x * other.x, self.y * other.y)


Vector = Vertex


class Zone(object):
    # __aspect_ratio = 1.25  # 5 / 4
    __aspect_ratio = 1  # 1 / 1
    __expand_ratio = 0.33

    def __init__(self, start_x, start_y,
                 width=None, height=None,
                 end_x=None, end_y=None,
                 bias_x=0, bias_y=0):
        self.start_x = int(start_x)
        self.start_y = int(start_y)
        if width is not None and height is not None:
            self.width = int(width)
            self.height = int(height)
            self.end_x = self.start_x + self.width
            self.end_y = self.start_y + self.height
        elif end_x is not None and end_y is not None:
            self.end_x = int(end_x)
            self.end_y = int(end_y)
            self.width = self.end_x - self.start_x
            self.height = self.end_y - self.start_y
        else:
            raise ValueError('Argument pair (width, height) or (end_x, end_y) '
                             'should be fully set. provided width={}, '
                             'height={}, end_x={}, end_y={}',
                             width, height, end_x, end_y)
        self.bias_x = bias_x
        self.bias_y = bias_y

    @decorator.CachedProperty
    def area(self):
        return self.width * self.height

    @decorator.CachedProperty
    def start_point(self):
        return Vertex(self.start_x, self.start_y)

    @decorator.CachedProperty
    def end_point(self):
        return Vertex(self.end_x, self.end_y)

    top_left = start_point
    bottom_right = end_point

    @decorator.CachedProperty
    def top_right(self):
        return Vertex(self.end_x, self.start_y)

    @decorator.CachedProperty
    def bottom_left(self):
        return Vertex(self.start_x, self.end_y)

    @decorator.CachedProperty
    def center(self):
        return Vertex(self.start_x + int(self.width / 2),
                      self.start_y + int(self.height / 2))

    @property
    def bias(self):
        return Vector(self.bias_x, self.bias_y)

    @bias.setter
    def bias(self, value):
        assert isinstance(value, collections.abc.Sized) and len(value) == 2
        assert isinstance(value, collections.abc.Iterable)
        self.bias_x, self.bias_y = value

    @decorator.CachedProperty
    def shape(self):
        return self.width, self.height

    def validate_shape(self, width, height):
        invalid_x = self.start_x < 0 and self.end_x > width
        invalid_y = self.start_y < 0 and self.end_y > height
        if invalid_x or invalid_y:
            raise ValueError(
                'Invalid zone config, start={}, size={}, frame size=[{}, {}]'.format(
                    self.start_point, self.shape, width, height))

    def move(self, x, y):
        """移动区域"""
        self.start_x += x
        self.start_y += y
        self.end_x = self.start_x + self.width
        self.end_y = self.start_y + self.height

    @decorator.CachedProperty
    def description(self):
        return {
            'x': self.start_x,
            'y': self.start_y,
            'w': self.width,
            'h': self.height,
            'x2': self.end_x,
            'y2': self.end_y,
            'bias_x': self.bias_x,
            'bias_y': self.bias_y
        }

    def get_zone(self, origin, bias_x=0, bias_y=0):
        """Get Cropped zone

        :param origin: full image frame
        :param bias_x: 裁剪图像区域时的横向偏移
        :param bias_y: 裁剪图像区域时的纵向偏移
        :return: cropped zone
        """
        if bias_x != 0 or bias_y != 0:
            self.move(bias_x, bias_y)
        result = origin[self.start_y:self.end_y, self.start_x:self.end_x]
        if bias_x != 0 or bias_y != 0:
            self.move(-bias_x, -bias_y)
        return result

    def expanded_zone(self, origin, bias_x=0, bias_y=0):
        """Get expanded zone with specific aspect ratio

        Face zone detected(Bounding box) with MTCNN is quite tight for viewing,
        we expand the detection zone out of displaying necessity.

        :param origin: 原始图像
        :param bias_x: 横轴方向偏移
        :param bias_y: 纵轴方向偏移
        :return: expanded zone
        """
        frame_height, frame_width, _ = origin.shape
        start_point, end_point = self.expanded_anchor(frame_width, frame_height,
                                                      bias_x, bias_y)
        result = origin[start_point.y:end_point.y, start_point.x:end_point.x]
        return result

    def expanded_anchor(self, frame_width, frame_height,
                        bias_x=0, bias_y=0,
                        aspect_ratio=None, max_expand_ratio=None) -> (Vertex, Vertex):
        """指定缩放比例获取图像扩张之后的关键点

        :param frame_width: 宽度限制
        :param frame_height: 高度限制
        :param bias_x: 包围盒偏移
        :param bias_y: 包围盒偏移
        :param aspect_ratio: 高宽比限制
        :param max_expand_ratio: 扩张比例限制
        :return 可扩展区域左上角点坐标和右下角点坐标
        """
        aspect_ratio = aspect_ratio if aspect_ratio else self.__aspect_ratio
        max_expand_ratio = max_expand_ratio if max_expand_ratio else self.__expand_ratio

        if bias_x != 0 or bias_y != 0:
            self.move(bias_x, bias_y)
        cur_aspect_ratio = self.height / self.width

        expand_ratio = min(frame_width / max(self.height / aspect_ratio, self.width),
                           frame_height / max(self.width * aspect_ratio, self.height))
        expand_ratio = min((expand_ratio - 1) / 2, max_expand_ratio)

        # 如果检测区域比较“矮胖”，先在横轴方向进行扩充
        if cur_aspect_ratio < aspect_ratio:
            resize_width = int((2 * expand_ratio + 1) * self.width)
            padding_left = int(expand_ratio * self.width)
            start_x = max(min(self.start_x - padding_left, frame_width - resize_width), 0)

            resize_height = int(resize_width * aspect_ratio)
            padding_top = int((resize_height - self.height) / 2)
            start_y = max(min(self.start_y - padding_top, frame_height - resize_height), 0)
        # 如果检测区域比较“高瘦”，先在纵轴方向进行扩充
        else:
            resize_height = int((2 * expand_ratio + 1) * self.height)
            padding_top = int(expand_ratio * self.height)
            start_y = max(min(self.start_y - padding_top, frame_height - resize_height), 0)

            resize_width = int(resize_height / aspect_ratio)
            padding_left = int((resize_width - self.width) / 2)
            start_x = max(min(self.start_x - padding_left, frame_width - resize_width), 0)

        end_x = start_x + resize_width
        end_y = start_y + resize_height
        if bias_x != 0 or bias_y != 0:
            self.move(-bias_x, -bias_y)
        return Vertex(start_x, start_y), Vertex(end_x, end_y)

    def __str__(self):
        return '[{}, {}], shape={}'.format(
            self.start_point, self.end_point, self.shape)

    def __repr__(self):
        return str(self)


class ImageFrame(object):
    """图像帧

    可以指定检测区域
    """

    def __init__(self, video_id, frame_id, frame=None,
                 zoom_ratio=1, zone: Zone = None):
        """缩放比例优先于检测区域，即检测区域是在缩放后的图像上选取"""
        self.video_id = video_id
        self.frame_id = frame_id
        self.frame = frame

        self.zoom_ratio = zoom_ratio
        self.zone = zone

        self.timestamp = int(time.time())
        self.extras = {}

    @decorator.CachedProperty
    def is_zoomed(self):
        return self.zoom_ratio > 0 and self.zoom_ratio != 1

    @decorator.CachedProperty
    def size(self):
        h, w, _ = self.frame.shape
        return w, h

    @decorator.CachedProperty
    def bias(self):
        if not self.zone:
            return 0, 0
        else:
            return self.zone.start_x, self.zone.start_y

    @decorator.CachedProperty
    def resized_size(self):
        """缩放后的图像尺寸：（宽，高）"""
        if not self.is_zoomed:
            return self.size
        else:
            return tuple(int(_ * self.zoom_ratio) for _ in self.size)

    @decorator.CachedProperty
    def resized_frame(self):
        """获取缩放后的图像帧"""
        if not self.is_zoomed:
            return self.frame
        else:
            return cv2.resize(self.frame, self.resized_size,
                              interpolation=cv2.INTER_CUBIC)

    @decorator.CachedProperty
    def detection_zone(self):
        """检测区域"""
        return self.zone.get_zone(self.resized_frame) if self.zone else self.resized_frame

    @decorator.CachedProperty
    def detection_zone_size(self):
        """检测区域尺寸"""
        h, w, _ = self.detection_zone.shape
        return w, h

    def extract_zone(self, zone: Zone):
        if not zone:
            return None
        bias_x, bias_y = self.bias
        return zone.get_zone(self.resized_frame, bias_x, bias_y)

    def extract_expanded_zone(self, zone: Zone):
        if not zone:
            return None
        bias_x, bias_y = self.bias
        return zone.expanded_zone(self.resized_frame, bias_x, bias_y)

    def __str__(self):
        return '{}-{}'.format(self.video_id, self.frame_id)

    def __repr__(self):
        return '{}: {}'.format(str(self), str(self.zone))


class Detection(Zone):
    """一个检测结果"""

    def __init__(self, start_x, start_y, end_x, end_y, rotation, *feature,
                 start_time=None):
        Zone.__init__(self, start_x, start_y, end_x=end_x, end_y=end_y)

        self.rotation = float(rotation)
        self.feature = np.array(feature)

        self.start_time = start_time
        self.end_time = time.perf_counter()

    @decorator.CachedProperty
    def elapsed(self):
        """检测耗费时间，单位为ms"""
        if self.start_time is None:
            return -1
        return int(1000.0 * (self.end_time - self.start_time))

    def __repr__(self):
        return str(self)
