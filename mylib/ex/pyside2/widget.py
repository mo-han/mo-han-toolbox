#!/usr/bin/env python3
from PySide2.QtWidgets import *

from mylib.ex.pyside2.style import *


def qt_text_label(s: str, parent=None, style=None):
    lb = QLabel(parent)
    lb.setText(s)
    if style:
        lb.setStyleSheet(qt_style_sheet(style))
    return lb
