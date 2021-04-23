#!/usr/bin/env python3
import getpass
import platform
import signal
import tempfile

from mylib.easy import *
from mylib.easy import tricks


def __refer_sth_do_not_use_this():
    return tricks


def ensure_sigint_signal():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'


TEMPDIR = tempfile.gettempdir()
HOSTNAME = platform.node()
OSNAME = platform.system()
USERNAME = getpass.getuser()