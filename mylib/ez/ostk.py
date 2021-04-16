#!/usr/bin/env python3
import signal

from mylib.ez import *
from mylib.ez import tricks


def __refer_sth_do_not_use_this():
    return tricks


def ensure_sigint_signal():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'
