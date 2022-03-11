#!/usr/bin/env python3
from io import *

from ezpykit.stdlib.io.slicefileio import *
from ezpykit.stdlib.io.virtualfileio import *

___ref = IOBase


class IOKit:
    @staticmethod
    def read_exit(x, *args, **kwargs):
        with x:
            return x.read(*args, **kwargs)

    @staticmethod
    def write_exit(x, *args, **kwargs):
        with x:
            return x.write(*args, **kwargs)
