#!/usr/bin/env python3
import getpass
import platform
import signal
import tempfile

from mylib.easy import *


def ensure_sigint_signal():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'


TEMPDIR = tempfile.gettempdir()
HOSTNAME = platform.node()
OSNAME = platform.system()
USERNAME = getpass.getuser()
