#!/usr/bin/env python3
from oldezpykit.metautil import ctx_ensure_module

with ctx_ensure_module('daemoniker'):
    from daemoniker import *

___ref = [Daemonizer]
