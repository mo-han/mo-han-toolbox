#!/usr/bin/env python3
import sys
from subprocess import *

from ezpykit.builtin import ezlist
from ezpykit.metautil import T

___ref = [run]

if sys.version_info < (3, 7):
    DETACHED_PROCESS = 0x00000008


class CommandLineList(ezlist):
    exec = None
    enable_option_with_multi_value = False
    force_option_with_equal_sign = False
    enable_short_option_for_word = False

    def __init__(self, *args, **kwargs):
        super().__init__()
        if self.exec and not args:
            self.add(self.exec)
        self.add(*args, **kwargs)

    def set_which(self, which):
        if self.exec and self.first == self.exec:
            self.exec = which
            self.first = which
        else:
            if self.exec:
                self.exec = which
            if self.first:
                self.first = which
        return self

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
            if self.enable_option_with_multi_value:
                self.add(name, *value)
            else:
                for v in value:
                    self.add_option(name, v)
        elif value is True:
            self.append(name)
        elif value is None or value is False:
            pass
        elif self.force_option_with_equal_sign:
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
        if (self.enable_short_option_for_word and '_' in key) or (
                not self.enable_short_option_for_word and len(key) > 1):
            opt_name = '--' + '-'.join(key.split('_'))
        else:
            opt_name = '-' + key
        return opt_name, value

    def popen(self, **kwargs) -> Popen:
        return Popen(self, **kwargs)

    def run(self, **kwargs):
        return run(self, **kwargs)


def popen_daemon_nt(*args, **kwargs):
    return Popen(*args, creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP, **kwargs)
