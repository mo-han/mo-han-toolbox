#!/usr/bin/env python3
from ezpykit.allinone import ctx_ensure_module

with ctx_ensure_module('yaml', 'PyYAML'):
    from yaml import *

___ref = safe_load
