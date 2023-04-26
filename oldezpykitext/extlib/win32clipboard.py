#!/usr/bin/env python3
from oldezpykit.metautil import ctx_ensure_module

with ctx_ensure_module('win32clipboard', 'pywin32'):
    from win32clipboard import *
    import win32clipboard

error = win32clipboard.error

___ref = OpenClipboard
