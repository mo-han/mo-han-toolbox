#!/usr/bin/env python3
# encoding=utf8
import inspect
import os
import re
import subprocess
from time import sleep

import pywintypes
import win32clipboard

from .tricks import Singleton, decorator_self_context

ILLEGAL_FS_CHARS = r'\/:*?"<>|'
ILLEGAL_FS_CHARS_LEN = len(ILLEGAL_FS_CHARS)
ILLEGAL_FS_CHARS_REGEX_PATTERN = re.compile(ILLEGAL_FS_CHARS)
ILLEGAL_FS_CHARS_UNICODE_REPLACE = r'⧹⧸꞉∗？″﹤﹥￨'
ILLEGAL_FS_CHARS_UNICODE_REPLACE_TABLE = str.maketrans(ILLEGAL_FS_CHARS, ILLEGAL_FS_CHARS_UNICODE_REPLACE)


class Clipboard(metaclass=Singleton):
    _wcb = win32clipboard
    cf_dict = {n.lstrip('CF_'): m for n, m in inspect.getmembers(_wcb) if n.startswith('CF_')}

    def __init__(self):
        self.delay = 0
        try:
            self._wcb.CloseClipboard()
        except pywintypes.error:
            pass
        finally:
            self.__opened = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def is_opened(self):
        return self.__opened

    @property
    def is_closed(self):
        return not self.__opened

    def open(self):
        if not self.__opened:
            sleep(self.delay)
            self._wcb.OpenClipboard()
            self.__opened = True

    def close(self):
        if self.__opened:
            self._wcb.CloseClipboard()
            # sleep(self.delay)  # maybe not needed
            self.__opened = False

    def valid_format(self, x: str or int):
        """get valid clipboard format ('CF_*')"""
        if isinstance(x, int):
            pass
        elif isinstance(x, str):
            x = x.upper()
            if not x.startswith('x_'):
                x = 'CF_' + x
            x = getattr(self._wcb, x)
        else:
            raise TypeError("'{}' is not str or int".format(x))
        return x

    @decorator_self_context
    def clear(self):
        return self._wcb.EmptyClipboard()

    @decorator_self_context
    def set(self, data, cf=_wcb.CF_UNICODETEXT):
        cf = self.valid_format(cf)
        return self._wcb.SetClipboardData(cf, data)

    @decorator_self_context
    def set_text(self, text):
        return self._wcb.SetClipboardText(text)

    @decorator_self_context
    def get(self, cf=_wcb.CF_UNICODETEXT):
        cf = self.valid_format(cf)
        if self._wcb.IsClipboardFormatAvailable(cf):
            data = self._wcb.GetClipboardData(cf)
        else:
            data = None
        return data

    def list_paths(self, exist_only=True) -> list:
        paths = self.get(self._wcb.CF_HDROP)
        if paths:
            if exist_only:
                return [p for p in paths if os.path.exists(p)]
            else:
                return list(paths)
        else:
            lines = [line.strip() for line in str(self.get()).splitlines()]
            return [line for line in lines if os.path.exists(line)]

    @decorator_self_context
    def get_all(self) -> dict:
        d = {}
        for k, v in self.cf_dict.items():
            if self._wcb.IsClipboardFormatAvailable(v):
                d[k] = self._wcb.GetClipboardData(v)
        return d


clipboard = Clipboard()


def fs_copy_cli(src, dst):
    subprocess.run(['copy', src, dst], shell=True).check_returncode()


def _fs_move_cli_move(src, dst):
    subprocess.run(['move', src, dst], shell=True).check_returncode()


def _fs_move_cli_robocopy(src, dst, quiet=True, verbose=False):
    full_log = verbose or not quiet
    args = ['robocopy']
    if not full_log:
        # https://stackoverflow.com/a/7487697/7966259
        # /NP  : No Progress - don't display percentage copied.
        # /NS  : No Size - don't log file sizes.
        # /NC  : No Class - don't log file classes.
        args.extend(['/NJH', '/NJS', '/NFL', '/NDL'])
    if os.path.isdir(src):
        args.extend(['/E', '/IS'])
    args.extend(['/MOVE', src, dst])
    subprocess.run(args, shell=True).check_returncode()


def fs_move_cli(src, dst, quiet=True, verbose=False):
    if os.path.isfile(src):
        _fs_move_cli_move(src, dst)
    elif os.path.isdir(src):
        _fs_move_cli_robocopy(src, dst, quiet=quiet, verbose=verbose)
    else:
        raise ValueError(src)
