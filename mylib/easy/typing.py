#!/usr/bin/env python3
from typing import *
from typing import IO, BinaryIO, TextIO


def __ref_sth():
    return IO, BinaryIO, TextIO


Decorator = Callable[[Callable], Callable]


class QueueType:
    def put(self, *args, **kwargs):
        ...

    def get(self, *args, **kwargs):
        ...


JSONType = Union[str, int, float, bool, None, Mapping[str, 'JSON'], List['JSON']]

NoneType = type(None)

EllipsisType = type(Ellipsis)
