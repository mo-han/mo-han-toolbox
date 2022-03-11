#!/usr/bin/env python3
import getpass
import pathlib
import platform
import queue
import signal
import subprocess
import sys
import tempfile
import time

from ezpykit.metautil import *
from ezpykit.builtin import *
from ezpykit.stdlib import io, os, argparse, threading, re, glob, shutil, base64

___ref = re, sys, subprocess, pathlib, glob, queue, threading, io, os, argparse, shutil, base64, ezdict

sleep = time.sleep

TEMPDIR = tempfile.gettempdir()
UNAME = platform.uname()
NETWORK_NAME = HOSTNAME = NODE_NAME = platform.node()
USERNAME = getpass.getuser()
OSNAME = platform.system()


def ensure_sigint():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'
