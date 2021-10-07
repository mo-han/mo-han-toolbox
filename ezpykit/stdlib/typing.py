#!/usr/bin/env python3
from typing import *
from typing import IO, BinaryIO, TextIO  # necessary!

from ezpykit.common.util_00 import helper_func_do_nothing

helper_func_do_nothing(IO, BinaryIO, TextIO)

EzDecorator = Callable[[Callable], Callable]


class EzQueueType:
    def put(self, *args, **kwargs):
        ...

    def get(self, *args, **kwargs):
        ...


EzJSONType = Union[str, int, float, bool, None, Mapping[str, 'JSON'], List['JSON']]

EzNoneType = type(None)

EzEllipsisType = type(Ellipsis)
