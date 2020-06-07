#!/usr/bin/env python3
# encoding=utf8

import os

if os.name == 'nt':
    from .xos_nt import *
elif os.name == 'posix':
    from .xos_posix import *
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
