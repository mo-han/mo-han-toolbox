#!/usr/bin/env python3
from os import *

if name == 'nt':
    from ezpykit.stdlib.os.nt import *
elif name == 'posix':
    from ezpykit.stdlib.os.posix import *
else:
    from ezpykit.stdlib.os.common import *
