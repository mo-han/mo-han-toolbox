#!/usr/bin/env python3
# encoding=utf8

import mouse


def module_pywinauto(disable_warning: bool = False, coinit: int = 2):
    """sys.coinit_flags=2 before import pywinauto
    https://github.com/pywinauto/pywinauto/issues/472"""
    if disable_warning:
        import warnings
        warnings.simplefilter('ignore', category=UserWarning)
    if coinit is not None:
        import sys
        sys.coinit_flags = coinit
    import pywinauto
    return pywinauto


def pywinauto_set_focus(pywinauto_object, homing_mouse: bool = True):
    if homing_mouse:
        original_coord = mouse.get_position()
        r = pywinauto_object.set_focus()
        mouse.move(*original_coord)
    else:
        r = pywinauto_object.set_focus()
    return r
