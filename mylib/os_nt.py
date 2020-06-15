#!/usr/bin/env python3
# encoding=utf8
import inspect
import re
import signal
import sys

from .struct import singleton

ILLEGAL_FS_CHARS = r'\/:*?"<>|'
ILLEGAL_FS_CHARS_LEN = len(ILLEGAL_FS_CHARS)
ILLEGAL_FS_CHARS_REGEX_PATTERN = re.compile(ILLEGAL_FS_CHARS)
ILLEGAL_FS_CHARS_SUBSTITUTES_UNICODE = r'⧹⧸꞉∗？″﹤﹥￨'
ILLEGAL_FS_CHARS_SUBSTITUTES_UNICODE_TABLE = str.maketrans(ILLEGAL_FS_CHARS, ILLEGAL_FS_CHARS_SUBSTITUTES_UNICODE)


@singleton
class Clipboard:
    import win32clipboard as wcb
    cf_dict = {n.lstrip('CF_'): m for n, m in inspect.getmembers(wcb) if n.startswith('CF_')}

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        self.wcb.OpenClipboard()

    def close(self):
        self.wcb.CloseClipboard()

    def valid_format(self, x: str or int):
        """get valid clipboard format ('CF_*')"""
        if isinstance(x, int):
            pass
        elif isinstance(x, str):
            x = x.upper()
            if not x.startswith('x_'):
                x = 'CF_' + x
            x = getattr(self.wcb, x)
        else:
            raise TypeError("'{}' is not str or int".format(x))
        return x

    def clear(self):
        return self.wcb.EmptyClipboard()

    def set(self, data, cf=wcb.CF_UNICODETEXT):
        cf = self.valid_format(cf)
        return self.wcb.SetClipboardData(cf, data)

    def set_text(self, text):
        return self.wcb.SetClipboardText(text)

    def get(self, cf=wcb.CF_UNICODETEXT):
        cf = self.valid_format(cf)
        if self.wcb.IsClipboardFormatAvailable(cf):
            data = self.wcb.GetClipboardData(cf)
        else:
            data = None
        return data

    def get_paths(self):
        paths = self.get(self.wcb.CF_HDROP)
        if paths:
            return list(paths)
        else:
            return []

    def get_all(self):
        d = {}
        for k, v in self.cf_dict.items():
            d[k] = self.get(v)
        return d


clipboard = Clipboard()


def win32_ctrl_c_signal():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'
