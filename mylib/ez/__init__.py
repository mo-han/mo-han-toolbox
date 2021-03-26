#!/usr/bin/env python3
# encoding=utf8
"""THIS MODULE MUST ONLY DEPEND ON STANDARD LIBRARIES OR BUILT-IN"""
import ctypes
import functools
import inspect
import io
import locale

from . import typing as _typing
from .often import *
from .shutil import shutil_ as shutil

T = _typing


def __refer_sth():
    return os, sys, time, sleep, shutil, re, io


class SingletonMetaClass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class AttrName(metaclass=SingletonMetaClass):
    def __setattr__(self, key, value):
        pass

    def __getattr__(self, item):
        return item


def str_remove_prefix(s: str, prefix: str):
    return s[len(prefix):] if s.startswith(prefix) else s


def str_remove_suffix(s: str, suffix: str):
    return s[:-len(suffix)] if s.endswith(suffix) else s


def get_os_default_locale():
    if os.name == 'nt':
        win_lang = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale[win_lang]
    else:
        return locale.getdefaultlocale()[0]


def deco_factory_copy_signature(signature_source: T.Callable):
    # https://stackoverflow.com/a/58989918/7966259
    def deco(target: T.Callable):
        @functools.wraps(target)
        def tgt(*args, **kwargs):
            inspect.signature(signature_source).bind(*args, **kwargs)
            return target(*args, **kwargs)

        tgt.__signature__ = inspect.signature(signature_source)
        return tgt

    return deco


def pip_install_dependencies(dep_list: T.List[str], update=False, user=True, options: list = ()):
    cmd = ['pip', 'install']
    if user:
        cmd.append('--user')
    if update:
        cmd.append('--update')
    cmd.extend(options)
    for dep in dep_list:
        subprocess.run([*cmd, dep])


class CLIArgumentsList(list):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.add(*args, **kwargs)

    def add_arg(self, arg):
        if isinstance(arg, str):
            self.append(arg)
        elif isinstance(arg, T.Iterable):
            for a in arg:
                self.add_arg(a)
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
            self.add_arg(arg)
        for k, v in kwargs.items():
            option_name = self.keyword_to_option_name(k)
            self.add_option(option_name, v)
        return self

    @staticmethod
    def keyword_to_option_name(keyword):
        if len(keyword) > 1:
            k = '--' + '-'.join(keyword.split('_'))
        else:
            k = '-' + keyword
        return k


def get_default_encoding():
    return locale.getdefaultlocale()[1]
