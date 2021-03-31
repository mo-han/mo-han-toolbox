#!/usr/bin/env python3
# encoding=utf8
"""THIS MODULE MUST ONLY DEPEND ON STANDARD LIBRARIES OR BUILT-IN"""
import ctypes
import functools
import importlib.util
import inspect
import io
import locale

from . import typing as _typing
from .__often_used_imports__ import *
from .shutil import shutil_ as shutil

T = _typing


def __refer_sth():
    return io, shutil


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


def get_os_default_lang(*, os_name=os.name):
    if os_name == 'nt':
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


def get_os_default_encoding():
    return locale.getdefaultlocale()[1]


def python_module_from_modified_source_code(
        module_path: str, new_source_code: str or T.Callable[[str], str], package_path: str = None,
        *, output: bool = False, output_file: str = 'tmp.py'):
    # How to modify imported source code on-the-fly?
    #     https://stackoverflow.com/a/41863728/7966259  (answered by Martin Valgur)
    # Modules and Packages: Live and Let Die!  (by David Beazley)
    #     http://www.dabeaz.com/modulepackage/ModulePackage.pdf
    #     https://www.youtube.com/watch?v=0oTh1CXRaQ0
    spec = importlib.util.find_spec(module_path, package_path)
    if isinstance(new_source_code, str):
        source = new_source_code
    else:
        source = new_source_code(spec.loader.get_source(module_path))
    if output:
        with open(output_file, 'w') as f:
            f.write(source)
    module = importlib.util.module_from_spec(spec)
    code_obj = compile(source, module.__spec__.origin, 'exec')
    exec(code_obj, module.__dict__)
    sys.modules[module_path] = module
    return module


def python_module_from_filepath(module_name, filepath):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Caller:
    def __init__(self, target, *args, **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def call(self):
        return self.target(*self.args, **self.kwargs)
