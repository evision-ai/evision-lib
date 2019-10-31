#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-31 09:47
# @version: 1.0
#
from evision.lib.util import DictUtil


def test_filter_values():
    map = {1: 2, 3: 4, 5: 6}
    map = {k: [v, ] for k, v in map.items()}
    filtered_map = DictUtil.filter_values(map, lambda x: x % 2 == 0)
    assert filtered_map == map
    filtered_map = DictUtil.filter_values(map, lambda x: x % 2 != 0)
    assert not filtered_map

    class Dummy(object):
        def __init__(dummy, value):
            dummy.value = value

        def is_odd(self):
            return self.value % 2 == 1

        def __eq__(self, other):
            return self.value == other.value

    map = {1: [Dummy(2), Dummy(3)], 2: [Dummy(4)]}
    filtered_map = DictUtil.filter_values(map, Dummy.is_odd)
    assert filtered_map == {1: [Dummy(3), ]}
