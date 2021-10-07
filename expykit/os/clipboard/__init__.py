#!/usr/bin/env python3
import os

if os.name == 'nt':
    from .nt import *
elif os.name == 'posix':
    from .posix import *
else:
    raise NotImplementedError
