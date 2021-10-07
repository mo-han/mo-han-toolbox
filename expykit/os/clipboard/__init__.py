#!/usr/bin/env python3
import os as _os

if _os.name == 'nt':
    from .nt import *
elif _os.name == 'posix':
    from .posix import *
else:
    raise NotImplementedError
