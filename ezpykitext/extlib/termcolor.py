#!/usr/bin/env python3
from ezpykit.allinone import ctx_ensure_module

with ctx_ensure_module('colorama'):
    import colorama

with ctx_ensure_module('termcolor'):
    from termcolor import *

colorama.init()

___ref = [cprint]
