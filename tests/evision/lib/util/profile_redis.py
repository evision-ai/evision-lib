#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-11-26 14:27
# @version: 1.0
#
import time

import numpy as np
from walrus import Database

from evision.lib.util.redis import RedisNdArrayQueue, RedisQueue


def profile_serialization(times=5):
    shape = (1080, 1920, 3)
    dtype = np.uint32
    frames = [np.ndarray(shape, dtype=dtype) for _ in range(times)]
    key = f'test:serialization:{int(time.time())}'

    time_start = time.time_ns()
    queue = RedisQueue(key, 24)
    [queue.put(frame) for frame in frames]
    [queue.get() for _ in range(times)]
    queue.destroy()
    time_end = time.time_ns()
    elapsed = time_end - time_start
    assert not Database().exists(key)
    print(f'Using pickle: {elapsed / 1000000000}s, avg: {elapsed / times / 1000000}ms')

    time.sleep(1)

    time_start = time.time_ns()
    queue = RedisNdArrayQueue(key, 24, shape, dtype)
    [queue.put(frame) for frame in frames]
    [queue.get() for _ in range(times)]
    queue.destroy()
    assert not Database().exists(key)
    time_end = time.time_ns()
    elapsed = time_end - time_start
    print(f'Using np.tobuffer: {elapsed / 1000000000}s, avg: {elapsed / times / 1000000}ms')


if __name__ == '__main__':
    profile_serialization()
