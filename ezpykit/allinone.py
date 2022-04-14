#!/usr/bin/env python3
import functools
import getpass
import json
import pathlib
import platform
import queue
import signal
import sys
import tempfile
import time

from ezpykit import call
from ezpykit import config
from ezpykit.builtin import *
from ezpykit.metautil import *
from ezpykit.stdlib import *

___ref = [pathlib, queue, ezstr, deco_singleton, T, os, call, config, functools, json]
___ref.extend([])

sleep = time.sleep

TEMPDIR = tempfile.gettempdir()
UNAME = platform.uname()
NETWORK_NAME = HOSTNAME = NODE_NAME = platform.node()
USERNAME = getpass.getuser()
OSNAME = platform.system()


def ensure_sigint():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'
