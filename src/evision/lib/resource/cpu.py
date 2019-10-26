#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Gong Dahan(gdh1995@evision.ai)
# @date: 2018-09-30 16:12
# @version: 1.0
#
import os
import sys

from evision.lib.log import logutil

try:
    import setproctitle as _setproctitle
except ImportError:
    _setproctitle = None
logger = logutil.get_logger()

__all__ = [
    'reserve',
    'select'
]

_proc_name = None


def get_proc_name():
    global _proc_name
    if _proc_name is None:
        if _setproctitle is None:
            _proc_name = os.path.basename(sys.argv[0])
        else:
            _proc_name = _setproctitle.getproctitle()
    return _proc_name


def reserve(wanted_cores, queue):
    cpu_list = []
    for _ in range(wanted_cores):
        cpu_id = queue.get()
        if queue.qsize() == 0:
            global _proc_name
            logger.info('[set-cpu] no enough cpu cores for {}: {} / {}, '
                        'reuse ids'.format(_proc_name, len(cpu_list),
                                           wanted_cores))
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            [queue.put(_i) for _i in range(1, cpu_count) if not queue.full()]
        cpu_list.append(cpu_id)
    return cpu_list


def select(cpu_list, all_=False, name=None):
    if not cpu_list and not all_:
        raise AttributeError('invalid cpu list: {}'.format(cpu_list))
    if cpu_list and all_:
        raise AttributeError('invalid argument all=True when cpu list is not empty')
    if os.name == 'nt':
        return
    import ctypes
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    # System dependent, see e.g. /usr/include/x86_64-linux-gnu/asm/unistd_64.h
    sys_gettid = 186
    pid = libc.syscall(sys_gettid)
    import subprocess
    cmd = ['taskset']
    cmd += ['-ap'] if all_ else [
        '-cp',
        ','.join(str(cpu) for cpu in cpu_list),
    ]
    cmd += [str(pid)]
    taskset = subprocess.run(cmd, stdout=subprocess.DEVNULL)
    if taskset.returncode != 0:
        logger.info('[set-cpu] #{} failed: {}'.format(name or get_proc_name(), taskset.returncode))
        return False
    logger.info('[set-cpu] #{} succeed: {}'.format(name or get_proc_name(), 'all' if all_ else cpu_list))
    return True
