#!/usr/bin/env python3
from ezpykit.allinone import subprocess


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

    def set_session(self, session_file, save_interval=None):
        self.add(i=session_file, save_session=session_file)
        if save_interval:
            self.add(save_session_interval=save_interval)
        return self

    def enable_rpc(self, port=None, secret=None, listen_all=False, allow_origin_all=False):
        self.add(enable_rpc=True)
        if port:
            self.add(rpc_listen_port=port)
        if secret:
            self.add(rpc_secret=secret)
        if listen_all:
            self.add(rpc_listen_all=listen_all)
        if allow_origin_all:
            self.add(rpc_allow_origin_all=allow_origin_all)
        return self
