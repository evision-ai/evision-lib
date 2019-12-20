#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-11-20 16:45
# @version: 1.0
#
import pickle
import time

from walrus import Database

from evision.lib.util.redis import RedisQueue

__test_key__ = f'redis-test-{time.time()}'


def remove_key(key):
    if Database().exists(key):
        Database().delete(key)


class TestRedisQueue(object):
    def setup_class(self):
        remove_key(__test_key__)
        self.queue = RedisQueue(__test_key__, 10, need_list_obj=True)
        self.val_queue = Database().List(__test_key__)

    def teardown_class(self):
        remove_key(self.queue.key)

    @staticmethod
    def teardown_method():
        remove_key(__test_key__)

    def test_put(self):
        print(self.queue.client)
        assert len(self.val_queue) == 0
        obj = dict(a=1, b=2)
        self.queue.put(str(obj))
        assert len(self.val_queue) == 1
        val_obj = self.val_queue[0]
        assert val_obj.decode() == str(obj)

    def test_empty(self):
        assert self.queue.empty()
        self.queue.put('a')
        assert not self.queue.empty()

    def test_size(self):
        assert self.queue.size() == 0
        self.queue.put('a')
        assert self.queue.size() == 1
        self.val_queue.pop()
        assert self.queue.size() == 0

    def test_peek(self):
        self.val_queue.prepend(pickle.dumps('a'))
        assert self.queue.peek() == 'a'
        self.val_queue.prepend(pickle.dumps('b'))
        assert self.queue.peek() == 'b'

    def test_get(self):
        self.val_queue.extend([pickle.dumps(_) for _ in [1, 2, 3, 4, 5]])
        assert self.queue.get() == [1, ]
        assert self.queue.get(5) == [1, 2, 3, 4, 5]
        assert not self.queue.get(100)

    def test_lrange(self):
        self.val_queue.extend([pickle.dumps(_) for _ in [1, 2, 3, 4, 5]])
        assert self.queue.lrange() == (5, [1, ])
        assert self.queue.lrange(5) == (5, [1, 2, 3, 4, 5])
        assert self.queue.lrange(100) == (5, [1, 2, 3, 4, 5])

    def test_destroy(self):
        mock_key = 'another-' + __test_key__
        queue = RedisQueue(mock_key, 10)
        queue.put('key')
        assert Database().exists(mock_key)
        assert queue.size() == 1
        queue.destroy()
        assert not Database().exists(mock_key)
