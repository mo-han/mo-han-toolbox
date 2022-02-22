#!/usr/bin/env python3
from os import *

if name == 'nt':
    from .nt import *
elif name == 'posix':
    from .posix import *
else:
    from .common import *
