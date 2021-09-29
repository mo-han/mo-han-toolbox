#!/usr/bin/env python3
from os import *

if name == 'nt':
    from ._nt import *
elif name == 'posix':
    from ._posix import *
else:
    from ._null import *
