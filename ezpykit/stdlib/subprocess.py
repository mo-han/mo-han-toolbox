#!/usr/bin/env python3
from subprocess import *

from ezpykit.builtin import ezlist
from ezpykit.stdlib.sub_init import T

___ref = [run]


class CommandLineList(ezlist):
    enable_single_option_multi_value = False

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.add(*args, **kwargs)

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
            if self.enable_single_option_multi_value:
                self.add(name, *value)
            else:
                for v in value:
                    self.add_option(name, v)
        elif value is True:
            self.append(name)
        elif value is None or value is False:
            pass
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

    @staticmethod
    def _kwarg_to_option(key, value):
        if len(key) > 1:
            opt_name = '--' + '-'.join(key.split('_'))
        else:
            opt_name = '-' + key
        return opt_name, value
