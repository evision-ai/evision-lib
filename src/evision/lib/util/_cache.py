# -*- coding: utf-8 -*-
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @version: 1.0
#
import string
import uuid

try:
    from random import choices
except ImportError:
    from random import choice

    def choices(population, k):
        return [choice(population) for _ in range(k)]

__all__ = [
    'CacheUtil'
]


class CacheUtil:
    @staticmethod
    def random_id():
        """获取随机ID"""
        return str(uuid.uuid4()).replace('-', '').lower()

    @staticmethod
    def random_string(length=16):
        """随机字符串"""
        return ''.join(choices(string.digits + string.ascii_letters, k=length))
