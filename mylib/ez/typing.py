#!/usr/bin/env python3
# encoding=utf8
from typing import *

Decorator = Callable[[Callable], Callable]


class QueueType:
    def put(self, *args, **kwargs):
        ...

    def get(self, *args, **kwargs):
        ...


JSONType = Union[str, int, float, bool, None, Mapping[str, 'JSON'], List['JSON']]

NoneType = type(None)

EllipsisType = type(Ellipsis)
