# -*- coding: utf-8 -*-
# @author: Chen Shijiang (chenshijiang@evision.ai)
# @version: 1.0
#
"""装饰器"""

from __future__ import print_function

import inspect
import time
from collections import namedtuple
from functools import wraps

__all__ = [
    'make_synchronized',
    'class_property',
    'timeit',
    'type_check',
    'CachedProperty',
    'Singleton'
]

try:
    from synchronize import make_synchronized
except ImportError:
    def make_synchronized(func):
        import threading

        func.__lock__ = threading.Lock()

        def synced_func(*args, **kws):
            with func.__lock__:
                return func(*args, **kws)

        return synced_func


class ClassPropertyDescriptor(object):
    """类属性"""

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, _class=None):
        if _class is None:
            _class = type(obj)
        return self.fget.__get__(obj, _class)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("Can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def class_property(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)


def timeit(func):
    """
    Decorator that reports the execution time.
    :param func: function to decorate
    :return: wrapped function
    """

    @wraps(func)
    def timed(*args, **kw):
        ts = time.time()
        result = func(*args, **kw)
        te = time.time()

        print('%r (%r, %r) %2.2f sec' % (func.__name__, args, kw, te - ts))
        return result

    return timed


class CachedProperty(object):
    """Decorator that converts a method with a single self argument into a
    property cached on the instance.

    Optional ``name`` argument allows you to make cached properties of other
    methods. (e.g.  url = cached_property(get_absolute_url, name='url') )
    """

    def __init__(self, func, name=None):
        self.func = func
        self.__doc__ = getattr(func, '__doc__')
        self.name = name or func.__name__

    def __get__(self, instance, cls=None):
        """
        Call the function and put the return value in instance.__dict__ so that
        subsequent attribute access on the instance returns the cached value
        instead of calling cached_property.__get__().
        """
        if instance is None:
            return self
        val = self.func(instance)
        setattr(instance, self.name, val)
        return val


class Singleton(type):
    """单例装饰"""

    def __init__(cls, name, bases, kwargs):
        super(Singleton, cls).__init__(name, bases, kwargs)
        cls._instance = None

    def __call__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__call__(*args, **kw)
        return cls._instance


def type_check(func):
    """类型检查装饰器"""
    msg = ('Expected type {expected!r} for argument {argument}, '
           'but got type {got!r} with value {value!r}')
    # 获取函数定义的参数
    sig = inspect.signature(func)
    parameters = sig.parameters  # 参数有序字典
    arg_keys = tuple(parameters.keys())  # 参数名称

    @wraps(func)
    def wrapper(*args, **kwargs):
        CheckItem = namedtuple('CheckItem', ('anno', 'arg_name', 'value'))
        check_list = []

        # collect args   *args 传入的参数以及对应的函数参数注解
        for i, value in enumerate(args):
            arg_name = arg_keys[i]
            anno = parameters[arg_name].annotation
            check_list.append(CheckItem(anno, arg_name, value))

        # collect kwargs  **kwargs 传入的参数以及对应的函数参数注解
        for arg_name, value in kwargs.items():
            anno = parameters[arg_name].annotation
            check_list.append(CheckItem(anno, arg_name, value))

        # check type
        for item in check_list:
            if not isinstance(item.value, item.anno):
                error = msg.format(expected=item.anno, argument=item.arg_name,
                                   got=type(item.value), value=item.value)
                raise TypeError(error)

        return func(*args, **kwargs)

    return wrapper
