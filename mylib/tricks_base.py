#!/usr/bin/env python3
# encoding=utf8
from typing import Callable


def constrained(x, x_type: Callable, x_condition: str or Callable = None, enable_default=False, default=None):
    x = x_type(x)
    if x_condition:
        if isinstance(x_condition, str) and eval(x_condition):
            return x
        elif isinstance(x_condition, Callable) and x_condition(x):
            return x
        elif enable_default:
            return default
        else:
            raise ValueError("'{}' conflicts with '{}'".format(x, x_condition))
    else:
        return x


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]