#!/usr/bin/env python3
from typing import *
from typing import IO, BinaryIO, TextIO, Match, Pattern  # necessary!

___ref = [IO, BinaryIO, TextIO, Match, Pattern]

T = TypeVar('T')  # Any type.
KT = TypeVar('KT')  # Key type.
VT = TypeVar('VT')  # Value type.
T_co = TypeVar('T_co', covariant=True)  # Any type covariant containers.
V_co = TypeVar('V_co', covariant=True)  # Any type covariant containers.
VT_co = TypeVar('VT_co', covariant=True)  # Value type covariant containers.
T_contra = TypeVar('T_contra', contravariant=True)  # Ditto contravariant.

NoneType = type(None)
EllipsisType = type(Ellipsis)

Decorator = Callable[[Callable], Callable]


class QueueType:
    def put(self, *args, **kwargs):
        ...

    def get(self, *args, **kwargs):
        ...


JSONType = Union[str, int, float, bool, None, Mapping[str, 'JSON'], List['JSON']]
