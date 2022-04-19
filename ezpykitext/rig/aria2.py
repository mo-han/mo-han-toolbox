#!/usr/bin/env python3
from ezpykit.allinone import subprocess


class Aria2CommandLineList(subprocess.CommandLineList):
    which = 'aria2c'

    def _kwarg_to_option(self, key, value):
        k, v = super()._kwarg_to_option(key, value)
        if v is False:
            return f'{k}=false', True
        return k, v

    def force_sequential(self, enable=True):
        return self.add(force_sequence=enable)

    def set_split(self, num=10, size='1M'):
        return self.add(s=num, x=num, k=size)

    def load_cookies_file(self, fp):
        return self.add(load_cookies=fp)

    def disable_async_dns(self):
        return self.add(async_dns=False)

    def set_dir(self, dp):
        return self.add(d=dp)

    def set_filename(self, fn):
        return self.add(o=fn)

    def disable_auto_rename(self):
        return self.add(auto_file_renaming=False)

    def set_quiet(self, enable=True):
        return self.add(quiet=enable)

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
