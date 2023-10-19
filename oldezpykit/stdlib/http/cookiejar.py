#!/usr/bin/env python3
import sys

if sys.version_info < (3, 10):
    from oldezpykit.stdlib.http.cookiejar_backport_from_cpython_v_3_10 import *
else:
    from http.cookiejar import *

__ref = MozillaCookieJar
