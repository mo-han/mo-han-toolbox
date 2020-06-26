#!/usr/bin/env python3
# encoding=utf8

import os
import shutil
import signal
import sys
import tempfile

if os.name == 'nt':
    from .osutil_nt import *
elif os.name == 'posix':
    from .osutil_posix import *
else:
    raise ImportError("Off-design OS: '{}'".format(os.name))


def legal_fs_name(x: str, repl: str or dict = None) -> str:
    if repl:
        if isinstance(repl, str):
            rl = len(repl)
            if rl > 1:
                legal = ILLEGAL_FS_CHARS_REGEX_PATTERN.sub(repl, x)
            elif rl == 1:
                legal = x.translate(str.maketrans(ILLEGAL_FS_CHARS, repl * ILLEGAL_FS_CHARS_LEN))
            else:
                legal = x.translate(str.maketrans('', '', ILLEGAL_FS_CHARS))
        elif isinstance(repl, dict):
            legal = x.translate(repl)
        else:
            raise ValueError("Invalid repl '{}'".format(repl))
    else:
        legal = x.translate(ILLEGAL_FS_CHARS_SUBSTITUTES_UNICODE_TABLE)
    return legal


def rename_helper(old_path: str, new: str, move_to: str = None, keep_ext: bool = True):
    old_root, old_basename = os.path.split(old_path)
    _, old_ext = os.path.splitext(old_basename)
    if move_to:
        new_path = os.path.join(move_to, new)
    else:
        new_path = os.path.join(old_root, new)
    if keep_ext:
        new_path = new_path + old_ext
    shutil.move(old_path, new_path)


def ensure_sigint_signal():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'


TEMPDIR = tempfile.gettempdir()