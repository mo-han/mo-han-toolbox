#!/usr/bin/env python3
# encoding=utf8
"""THIS MODULE MUST ONLY DEPEND ON STANDARD LIBRARIES OR BUILT-IN"""
import ctypes
import functools
import inspect
import locale
import os
import queue
import re
import shutil
import sys
import subprocess
import threading
import time
from time import sleep

from . import typing

global_config = {'shutil.copy.buffer.size': 16 * 1024 * 1024}


def __refer_sth():
    return os, sys, time, sleep, shutil, re


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


def shutil_copy_file_obj_fast(src_fd, dst_fd, length: int = None):
    length = length or global_config['shutil.copy.buffer.size']
    while 1:
        buf = src_fd.read(length)
        if not buf:
            break
        dst_fd.write(buf)


def shutil_copy_file_obj_faster(src_fd, dst_fd, length: int = None):
    length = length or global_config['shutil.copy.buffer.size']
    q_max = 2
    q = queue.Queue(maxsize=q_max)
    stop = threading.Event()
    data_array = [0.0]

    def read():
        t0 = time.perf_counter()
        while 1:
            if stop.isSet():
                break
            t1 = time.perf_counter()
            td = t1 - t0
            t0 = t1
            if q.qsize() == q_max:
                sleep(td)
                continue
            buf = src_fd.read(length)
            if buf:
                q.put(buf)
            else:
                q.put(None)
                break

    def write():
        t0 = time.perf_counter()
        while 1:
            if stop.isSet():
                break
            t1 = time.perf_counter()
            td = t1 - t0
            data_array[0] = td
            t0 = t1
            try:
                buf = q.get()
            except queue.Empty:
                sleep(td)
                continue
            if buf is None:
                break
            else:
                dst_fd.write(buf)

    t_read = threading.Thread(target=read)
    t_write = threading.Thread(target=write)
    t_read.start()
    t_write.start()
    try:
        while 1:
            if t_write.is_alive():
                t_write.join(data_array[0])
            else:
                break
    except (KeyboardInterrupt, SystemExit):
        stop.set()
        raise


shutil.copyfileobj = shutil_copy_file_obj_faster


def deco_factory_copy_signature(signature_source: typing.Callable):
    # https://stackoverflow.com/a/58989918/7966259
    def deco(target: typing.Callable):
        @functools.wraps(target)
        def tgt(*args, **kwargs):
            inspect.signature(signature_source).bind(*args, **kwargs)
            return target(*args, **kwargs)

        tgt.__signature__ = inspect.signature(signature_source)
        return tgt

    return deco


def pip_install_dependencies(dep_list, update=False, user=True, options: list = ()):
    cmd = ['pip', 'install']
    if user:
        cmd.append('--user')
    if update:
        cmd.append('--update')
    cmd.extend(options)
    for dep in dep_list:
        subprocess.run([*cmd, dep])
