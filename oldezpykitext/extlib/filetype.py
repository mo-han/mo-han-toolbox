#!/usr/bin/env python3
from oldezpykit.allinone import ctx_ensure_module

with ctx_ensure_module('filetype'):
    from filetype import *

___ref = guess_mime
