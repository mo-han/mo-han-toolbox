#!/usr/bin/env python3
# encoding=utf8
"""THIS MODULE MUST ONLY DEPEND ON STANDARD LIBRARIES OR BUILT-IN"""
import os
import re
import shutil
import sys
import time
from time import sleep

assert os
assert sys
assert time
assert sleep
assert shutil
assert re


class SingletonMetaClass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class AttrToStr(metaclass=SingletonMetaClass):
    def __setattr__(self, key, value):
        pass

    def __getattr__(self, item):
        return item


def rm_str_start_by_split(s, start):
    return s.split(start, maxsplit=1)[-1]


def rm_str_end_by_rsplit(s, end):
    return s.rsplit(end, maxsplit=1)[0]
