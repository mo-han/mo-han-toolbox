#!/usr/bin/env python3
from ezpykit.allinone import *


class Aria2CommandLineList(subprocess.CommandLineList):
    def __init__(self, which='aria2c', *args, **kwargs):
        super().__init__(which, *args, **kwargs)

    def _kwarg_to_option(self, key, value):
        k, v = super()._kwarg_to_option(key, value)
        if v is False:
            return f'{k}=false', True
        return k, v

    def force_sequential(self, enable=True):
        self.add(force_sequence=enable)
        return self

    def set_split(self, num=10, size='1M'):
        self.add(s=num, x=num, k=size)
        return self

    def load_cookies_file(self, fp):
        self.add(load_cookies=fp)
        return self

    def disable_async_dns(self):
        self.add(async_dns=False)
        return self

    def set_dir(self, dp):
        self.add(d=dp)
        return self

    def set_filename(self, fn):
        self.add(o=fn)
        return self

    def disable_auto_rename(self):
        self.add(auto_file_renaming=False)
        return self

    def set_quiet(self, enable=True):
        self.add(quiet=enable)
        return self

    def add_uri(self, uri):
        self.add(uri)
        return self
