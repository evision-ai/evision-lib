#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-11-20 16:30
# @version: 1.0
#
import pickle
import time
from queue import Queue

from walrus import Database


class RedisQueue(object):
    def __init__(self, key, queue_size):
        self.queue_size = queue_size
        self.client = Database()
        self.key = key
        self.queue = self.client.List(key)

    def put(self, frame):
        pipe = self.client.pipeline()
        pipe.lpush(self.key, pickle.dumps(frame))
        pipe.ltrim(self.key, 0, self.queue_size)
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
        return pickle.loads(item)

    def get(self, expected_size=1):
        if expected_size < 1:
            return None
        pipe = self.client.pipeline()
        pipe.llen(self.key)
        pipe.lrange(self.key, 0, expected_size - 1)
        size, items = pipe.execute()
        if size < expected_size:
            return None
        return [pickle.loads(item) for item in items]

    def lrange(self, expected_size=1):
        pipe = self.client.pipeline()
        pipe.llen(self.key)
        pipe.lrange(self.key, 0, expected_size - 1)
        len_queue, items = pipe.execute()
        return len_queue, [pickle.loads(item) for item in items]

    def destroy(self):
        self.client.delete(self.key)


class RedisUtil(object):
    @staticmethod
    def mirror_queue(queue: Queue, key, size=24):
        mirror = RedisQueue(key, size)
        print(f'mirroring to redis list: {key}')
        while True:
            if queue is None or queue.empty():
                time.sleep(0.1)
                continue
            mirror.put(queue.queue[0])
