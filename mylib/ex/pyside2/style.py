#!/usr/bin/env python3
from PySide2.QtCore import QMargins
from PySide2.QtWidgets import QWidget
from mylib.easy import T


def ez_qss(style, selector=None):
    if isinstance(style, dict):
        style_sheet = '; '.join(f'{k.replace("_", "-")}: {v}' for k, v in style.items())
    elif isinstance(style, str):
        style_sheet = style
    elif isinstance(style, T.Iterable):
        style_sheet = '; '.join(i for i in style)
    else:
        raise TypeError('style')
    if selector:
        if hasattr(selector, '__name__'):
            selector = selector.__name__
        style_sheet = f'{selector} {{{style_sheet}}}'
    return style_sheet


def ez_qss_set(qt_obj, style, selector=None):
    qss = ez_qss(style, selector)
    print(qss)
    qt_obj.setStyleSheet(qss)
