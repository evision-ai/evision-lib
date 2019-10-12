#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 eVision.ai Inc. All Rights Reserved.
#
# @author: Chen Shijiang(chenshijiang@evision.ai)
# @date: 2019-10-12 12:54
# @version: 1.0


class ModelIsNone(ValueError):
    def __init__(self):
        ValueError.__init__(self, 'Model should be provided')


class ModelOfWrongType(ValueError):
    def __init__(self, type_):
        ValueError.__init__(
            self, 'peewee.Model is required, provided is {}'.format(type_))
