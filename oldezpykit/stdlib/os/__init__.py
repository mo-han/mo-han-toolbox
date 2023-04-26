#!/usr/bin/env python3
from os import *

if name == 'nt':
    from oldezpykit.stdlib.os.nt import *
elif name == 'posix':
    from oldezpykit.stdlib.os.posix import *
else:
    from oldezpykit.stdlib.os.common import *
