#!/usr/bin/env python3
# encoding=utf8
import os
import re
import subprocess

from .tricks import singleton

ILLEGAL_FS_CHARS = r'/'
ILLEGAL_FS_CHARS_LEN = len(ILLEGAL_FS_CHARS)
ILLEGAL_FS_CHARS_REGEX_PATTERN = re.compile(ILLEGAL_FS_CHARS)
ILLEGAL_FS_CHARS_SUBSTITUTES_UNICODE = r'⧸'
ILLEGAL_FS_CHARS_SUBSTITUTES_UNICODE_TABLE = str.maketrans(ILLEGAL_FS_CHARS, ILLEGAL_FS_CHARS_SUBSTITUTES_UNICODE)


@singleton
class Clipboard:
    import pyperclip as _cb

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def set(self, data):
        self._cb.copy(data)

    def get(self):
        return self._cb.paste()

    def list_paths(self, exist_only=True):
        lines = [line.strip() for line in str(self.get()).splitlines()]
        return [line for line in lines if os.path.exists(line)]


clipboard = Clipboard()


def fs_copy_cli(src, dst):
    return subprocess.run(['cp', '-r', src, dst], shell=True)


def fs_move_cli(src, dst):
    return subprocess.run(['mv', src, dst], shell=True)
