#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-18 15:14
# @version: 1.0
#
import sys

__all__ = [
    'SysUtil'
]


class SysUtil(object):
    @staticmethod
    def disable_sys_stdin():
        try:
            if not sys.stdin.closed:
                sys.stdin.close()
        except Exception:
            pass
