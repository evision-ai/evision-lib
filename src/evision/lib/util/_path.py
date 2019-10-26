# -*- coding: utf-8 -*-
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @version: 1.0

import os
import sys
from os import path as osp

__all__ = [
    'PathUtil'
]


class PathUtil(object):
    @staticmethod
    def add_path(path):
        if path not in sys.path:
            sys.path.insert(0, path)

    @staticmethod
    def get_ext(_filename):
        if _filename is None:
            return None
        return os.path.splitext(_filename)[-1]

    @staticmethod
    def check_exists(*paths):
        """
        check whether all paths exist
        :param paths:
        :return:
        """
        for _path in paths:
            if not osp.exists(_path):
                return False
        return True

    @staticmethod
    def check_directory(_directory):
        """Check whether directory exists
        if not, create it
        :param _directory: path of directory to be checked
        """
        if not osp.exists(_directory) or not osp.isdir(_directory):
            os.makedirs(_directory)

    @staticmethod
    def ensure_directory(*outer_args):
        """Decorator for ensure directory exists
        """

        def _ensure_directory(func):
            def do_func(*inner_args, **kwargs):
                _directory = outer_args[0] if outer_args else inner_args[1] if \
                    inner_args[1:] else kwargs.get('directory')
                if not _directory:
                    raise FileNotFoundError('No directory specified for checking')
                PathUtil.check_directory(_directory)
                result = func(*inner_args, **kwargs)
                return result

            return do_func

        return _ensure_directory


def print_vars():
    tmp = globals().copy()
    for k, v in sorted(tmp.items()):
        if k.startswith('_') or hasattr(v, '__call'):
            continue
        if k in ('tmp', 'In', 'Out'):
            continue
        print('{}:\t{}, type:{}'.format(k, v, type(v)))


if __name__ == '__main__':
    print_vars()

__END__ = True
