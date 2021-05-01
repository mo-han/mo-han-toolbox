#!/usr/bin/env python3
from PySide2.QtCore import *
from PySide2.QtWidgets import *

from mylib.easy import *


def ___():
    return QCoreApplication


@deco_cached_call
def get_qt_application_singleton(argv=None):
    argv = argv or sys.argv
    return QApplication(argv)
