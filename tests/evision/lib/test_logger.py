# -*- coding: utf-8 -*-
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @date: 2018-06-09 15:36
# @version: 1.0
#

from evision.lib.log import logutil

logger = logutil.get_logger()


def test_logger():
    logger.debug('')
    logger.info('')
    logger.info('{}', 'haha')
    logger.info('{}', 1)
    try:
        raise ValueError('value error message')
    except Exception as e:
        logger.exception('{}, {}', 'a', e)
    logger.error('{}', 'a', ValueError('1'))
    logger.warning('{}', 'warning')
