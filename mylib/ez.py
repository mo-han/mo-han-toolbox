#!/usr/bin/env python3
# encoding=utf8
"""THIS MODULE MUST ONLY DEPEND ON STANDARD LIBRARIES OR BUILT-IN"""
import os
import re
import shutil
import sys
from time import time, sleep
from typing import *

assert os
assert sys
assert time
assert sleep
assert shutil
assert re

Decorator = Callable[[Callable], Callable]


class QueueType:
    def put(self, *args, **kwargs):
        ...

    def get(self, *args, **kwargs):
        ...


JSONType = Union[str, int, float, bool, None, Mapping[str, 'JSON'], List['JSON']]


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]