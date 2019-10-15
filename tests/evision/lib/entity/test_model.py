# -*- coding: utf-8 -*-
#
# Copyright 2018 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-07-24 10:52
# @version: 1.0
#
import collections
import os
from os import path as osp

import cv2
import numpy as np
import pytest

from evision.lib.entity import ImageFrame, Vertex, Zone
from evision.lib.log import logutil

logger = logutil.get_logger()


def get_test_image():
    test_image = cv2.imread(osp.join(osp.dirname(__file__), 'test.jpg'))
    assert test_image is not None
    test_image = cv2.resize(test_image, (540, 800))
    return test_image


def test_single_vertex():
    x, y = 100, 50
    vertex = Vertex(x, y)

    assert vertex.to_list() == [x, y]
    assert vertex.to_tuple() == (x, y)
    assert str(vertex) == '({}, {})'.format(x, y)

    # __eq__
    assert vertex == Vertex(x, y)
    assert vertex == [x, y]
    assert vertex == (x, y)

    # __len__
    assert len(vertex) == 2

    # __iter__
    assert isinstance(vertex, collections.Iterable)

    # times
    vertex = vertex.times(2)
    assert vertex == [x * 2, y * 2]

    vertex = Vertex(0, 0)
    assert len(vertex) == 2
    vertex = Vertex(0, None)
    assert len(vertex) == 0


def test_multiple_vertex():
    x, y = 100, 50
    vertex = Vertex(x, y)

    other = Vertex(-50, 50)

    assert (vertex + other) == Vertex(50, 100)
    assert (vertex - other) == Vertex(150, 0)


def test_zone():
    x, y, x2, y2 = 30, 20, 930, 520
    width, height = 900, 500
    zone = Zone(x, y, end_x=x2, end_y=y2)
    assert zone.width == width
    assert zone.height == height
    assert zone.area == width * height
    assert zone.start_point == (x, y)
    assert zone.end_point == (x2, y2)
    assert zone.shape == (width, height)
    zone.validate_shape(960, 540)

    zone.move(-10, -10)
    assert zone.start_x == 20
    assert zone.start_y == 10
    assert zone.end_x == 920
    assert zone.end_y == 510
    assert zone.width == width
    assert zone.height == height


def test_zone_expanding():
    width, height = 900, 500
    zone_width, zone_height = 100, 50

    x, y = 400, 225
    zone = Zone(x, y, width=zone_width, height=zone_height)
    start, end = zone.expanded_anchor(width, height,
                                      aspect_ratio=0.5, max_expand_ratio=0.5)
    logger.debug('expand vertex fro zone={}: start={}, end={}', zone, start, end)
    assert start == (350, 200)
    assert end == (550, 300)

    zone = Zone(0, 0, width=zone_width, height=zone_height)
    start, end = zone.expanded_anchor(width, height,
                                      aspect_ratio=0.5, max_expand_ratio=0.5)
    logger.debug('expand vertex fro zone={}: start={}, end={}', zone, start, end)
    assert start == (0, 0)
    assert end == (200, 100)

    zone = Zone(30, 20, width=zone_width, height=zone_height)
    start, end = zone.expanded_anchor(width, height,
                                      aspect_ratio=0.5, max_expand_ratio=0.5)
    logger.debug('expand vertex fro zone={}: start={}, end={}', zone, start, end)
    assert start == (0, 0)
    assert end == (200, 100)

    zone = Zone(0, 0, width=zone_width, height=zone_height)
    start, end = zone.expanded_anchor(width, height,
                                      bias_x=400, bias_y=225,
                                      aspect_ratio=0.5, max_expand_ratio=0.5)
    logger.debug('expand vertex fro zone={}: start={}, end={}', zone, start, end)
    assert start == (350, 200)
    assert end == (550, 300)
    assert zone.start_point == (0, 0)
    assert zone.end_point == (zone_width, zone_height)


def test_no_zoom_frame():
    test_image = get_test_image()
    height, width, _ = test_image.shape
    logger.info('Frame size: {}, {}', width, height)
    cv2.imwrite('test.png', test_image)
    os.remove('test.png')
    padding = 30
    zone = Zone(padding, padding,
                end_x=width - padding, end_y=height - padding)
    frame = ImageFrame('video_id', 'frame_id', frame=test_image,
                       zoom_ratio=1, zone=zone)

    assert not frame.is_zoomed
    assert frame.size
    resized_frame = frame.resized_frame
    resized_frame2 = frame.resized_frame
    assert id(resized_frame) == id(frame.frame)
    assert id(resized_frame) == id(resized_frame2)

    assert frame.size == (width, height)
    assert frame.bias == (padding, padding)
    assert frame.resized_size == frame.size

    detection_zone = frame.detection_zone
    assert isinstance(detection_zone, np.ndarray)
    assert detection_zone.shape[:2] == (height - 2 * padding, width - 2 * padding)


@pytest.mark.skip(reason="should test image frame zooming manually")
def test_zoomed_frame():
    test_image = get_test_image()
    height, width, _ = test_image.shape
    zoom_ratio = 0.5
    resize_height = int(height * zoom_ratio)
    resize_width = int(width * zoom_ratio)
    padding_x, padding_y = 30, 50
    zone = Zone(padding_x, padding_y,
                end_x=resize_width - padding_x, end_y=resize_height - padding_y)
    frame = ImageFrame('video_id', 'frame_id', frame=test_image,
                       zoom_ratio=zoom_ratio, zone=zone)

    extract_start = Vertex(100, 100)
    extract_shape = Vertex(130, 100)
    extract = Zone(*extract_start, *extract_shape)

    assert frame.is_zoomed
    assert frame.size
    assert frame.size == (width, height)
    assert frame.bias == (padding_x, padding_y)
    assert frame.resized_size == (width * zoom_ratio, height * zoom_ratio)

    resized_frame = frame.resized_frame
    resized_frame2 = frame.resized_frame
    assert resized_frame.shape[:2] == (resize_height, resize_width)
    assert id(resized_frame) == id(resized_frame2)
    cv2.imwrite('resized_frame_file.jpg', resized_frame)

    detection_zone = frame.detection_zone
    assert isinstance(detection_zone, np.ndarray)
    assert detection_zone.shape[:2] == (resize_height - padding_y * 2,
                                        resize_width - padding_x * 2)
    cv2.rectangle(detection_zone,
                  extract_start.to_tuple(),
                  (extract_start + extract_shape - (1, 1)).to_tuple(),
                  (255, 0, 0))
    cv2.imwrite('detection_frame_file.jpg', detection_zone)

    cv2.imwrite('extract_zone_file.jpg', frame.extract_zone(extract))
    logger.info('expanded size: {}, {}', *(extract.expanded_anchor(
        resize_width, resize_height, padding_x, padding_y)))
    cv2.imwrite('extract_expanded_zone_file.jpg',
                frame.extract_expanded_zone(extract))


if __name__ == '__main__':
    test_zoomed_frame()
