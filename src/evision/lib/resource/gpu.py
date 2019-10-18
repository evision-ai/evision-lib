#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Gong Dahan(gdh1995@evision.ai)
# @date: 2018-09-30 16:12
# @version: 1.0
import os

from evision.lib.log import logutil
from evision.lib.log.logconfig import Loggers

logger = logutil.get_logger(Loggers.CONSOLE)
_ALL_VISIBLE = False
_RAND = False

__all__ = [
    'setup_gpu_index',
    'get_gpu_memory_status',
    'get_gpu_status'
]


def setup_gpu_index(gpu_id):
    key = 'CUDA_VISIBLE_DEVICES'
    global _ALL_VISIBLE
    if _ALL_VISIBLE is False:
        _ALL_VISIBLE = os.environ.get(key, None)
    if _ALL_VISIBLE == '':  # disabled
        logger.info("[gpu] disabled globally, so {} is not usable".format(gpu_id))
        return
    allowed = _ALL_VISIBLE.split(",") if _ALL_VISIBLE else None
    index = max(0, min(gpu_id, len(allowed) if allowed else 16))
    if _RAND:
        import random
        index = random.randint(0, len(allowed) if allowed else 16)
    os.environ[key] = str(index)
    logger.info("[gpu] select {}".format(index))


def get_gpu_memory_status():
    """
    获取 GPU 显存使用情况
    :return: unit: MB
    """
    ret_free = os.popen('nvidia-smi -q -d Memory | grep -A4 GPU | grep Free').readlines()
    return [int(gpu_memory.split()[2]) for gpu_memory in ret_free]


def get_gpu_status():
    """
    获取 GPU 显存使用情况
    :return:
    """
    ret = []
    ret_total = os.popen('nvidia-smi -q -d Memory | grep -A4 GPU | grep Total').readlines()
    ret_free = os.popen('nvidia-smi -q -d Memory | grep -A4 GPU | grep Free').readlines()
    for i, total_memory in enumerate(ret_total):
        tmp_free = ret_free[i]
        ret.append([int(tmp_free.split()[2]), int(total_memory.split()[2])])
    return ret


if __name__ == '__main__':
    logger.info(get_gpu_memory_status())
    logger.info(get_gpu_status())
    pass
