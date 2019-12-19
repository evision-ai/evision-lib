#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-11-20 16:30
# @version: 1.0
#
import os
import pickle
import time
from queue import Queue
from typing import List, Tuple, Union

import numpy as np
from numpy import ndarray as nda
from redis import Redis
from walrus import Database


class RedisQueue(object):
    def __init__(self, key: str, queue_size=-1, alive_time=360, redis_client: Redis = None):
        self.queue_size = int(queue_size)
        if redis_client:
            self.client = redis_client
        elif os.getenv('REDIS_URL'):
            self.client = Database.from_url(os.getenv('REDIS_URL'))
        else:
            self.client = Database(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=os.getenv('REDIS_PORT', '6379'),
                password=os.getenv('REDIS_PASSWORD')
            )
        self.key = key
        # FIXME: @gdh1995 啥意思？
        self.queue = self.client.List(key) if self.queue_size < 0 else None
        self.alive_time = alive_time

    serialize = pickle.dumps
    deserialize = pickle.loads

    def put(self, frame,
            extra_data: List[Tuple[str, Union[bytes, str], int]] = None):
        if self.queue is not None:
            if extra_data:
                raise NotImplementedError('Don\'t support extra data')
            self.queue.prepend(frame)
        else:
            pipe = self.client.pipeline()
            for ex_key, ex_val, ex_expired_time in extra_data:
                pipe.set(ex_key, ex_val)
                pipe.expire(ex_key, ex_expired_time)
            pipe.lpush(self.key, self.serialize(frame))
            pipe.ltrim(self.key, 0, self.queue_size)
            pipe.expire(self.key, 86400)
            pipe.execute()

    def empty(self):
        return self.queue is None or not self.queue

    def size(self):
        return len(self.queue)

    def peek(self):
        pipe = self.client.pipeline()
        pipe.llen(self.key)
        pipe.lindex(self.key, 0)
        size, item = pipe.execute()
        if size == 0:
            return None
        return self.deserialize(item)

    def get(self, expected_size=1):
        if expected_size < 1:
            return None
        pipe = self.client.pipeline()
        pipe.llen(self.key)
        pipe.lrange(self.key, 0, expected_size - 1)
        size, items = pipe.execute()
        if size < expected_size:
            return None
        return [self.deserialize(item) for item in items]

    def lrange(self, expected_size=1):
        pipe = self.client.pipeline()
        pipe.llen(self.key)
        pipe.lrange(self.key, 0, expected_size - 1)
        len_queue, items = pipe.execute()
        return len_queue, [self.deserialize(item) for item in items]

    def destroy(self):
        self.client.delete(self.key)


class RedisNdArrayQueue(RedisQueue):
    def __init__(self, key, size, frame_shape, dtype=np.uint8):
        super().__init__(key, size)

        if frame_shape is not None:
            if None in frame_shape:
                raise ValueError(f'Invalid frame shape: {frame_shape}')
            self.frame_shape = tuple(int(_) for _ in frame_shape)
            self.dtype = dtype

    @staticmethod
    def serialize(array):
        return nda.tobytes(array)

    def deserialize(self, array_bytes):
        return np.frombuffer(array_bytes, dtype=self.dtype).reshape(self.frame_shape)


class RedisNdArrayQueueReader(RedisNdArrayQueue):
    put = None
    destroy = None


class RedisNdArrayQueueWriter(RedisNdArrayQueue):
    def __init__(self, key, size):
        super().__init__(key, size, None)

    peek = None
    get = None
    lrange = None


class RedisUtil(object):
    @staticmethod
    def mirror_queue(queue: Queue, key, size=24):
        mirror = RedisQueue(key, size)
        while True:
            if queue is None or queue.empty():
                time.sleep(0.1)
                continue
            mirror.put(queue.queue[0])

    @staticmethod
    def mirror_arrays(queue: Queue, key, size=24):
        mirror = RedisNdArrayQueueWriter(key, size)
        while True:
            if queue is None or queue.empty():
                time.sleep(0.1)
                continue
            mirror.put(queue.queue[0])

    @staticmethod
    def remove_key(key):
        if Database().exists(key):
            Database().delete(key)
