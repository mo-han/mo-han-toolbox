#!/usr/bin/env python3
from oldezpykit.allinone import ctx_ensure_module

with ctx_ensure_module('retrying'):
    from retrying import *

___ref = retry
