#!/usr/bin/env python3
import sys
from subprocess import *

from ezpykit.builtin import ezlist
from ezpykit.metautil import T

___ref = [run]

if sys.version_info < (3, 7):
    DETACHED_PROCESS = 0x00000008


class CommandLineList(ezlist):
    which = None
    enable_option_multi_value = False
    enable_option_equal_sign = False
    

    def __init__(self, *args, **kwargs):
        super().__init__()
        if self.which:
            self.add(self.which)
        self.add(*args, **kwargs)

    def copy(self: T.VT) -> T.VT:
        new = self.__class__(self)
        return new

    def add_argument(self, arg):
        if isinstance(arg, str):
            self.append(arg)
        elif isinstance(arg, T.Iterable):
            for a in arg:
                self.add_argument(a)
        else:
            self.append(str(arg))
        return self

    def add_option(self, name: str, value):
        if not isinstance(name, str):
            raise TypeError('name', str)
        if isinstance(value, str):
            self.append(name)
            self.append(value)
        elif isinstance(value, T.Iterable):
            if self.enable_option_multi_value:
                self.add(name, *value)
            else:
                for v in value:
                    self.add_option(name, v)
        elif value is True:
            self.append(name)
        elif value is None or value is False:
            pass
        elif self.enable_option_equal_sign:
            self.append(f'{name}={value}')
        else:
            self.append(name)
            self.append(str(value))
        return self

    def add(self, *args, **kwargs):
        for arg in args:
            self.add_argument(arg)
        for k, v in kwargs.items():
            self.add_option(*self._kwarg_to_option(k, v))
        return self

    def _kwarg_to_option(self, key, value):
        if len(key) > 1:
            opt_name = '--' + '-'.join(key.split('_'))
        else:
            opt_name = '-' + key
        return opt_name, value

    def popen(self, **kwargs):
        return Popen(self, **kwargs)


def popen_daemon_nt(*args, **kwargs):
    return Popen(*args, creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP, **kwargs)
