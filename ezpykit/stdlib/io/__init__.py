#!/usr/bin/env python3
from io import *

from ezpykit.stdlib.io.slicefileio import *
from ezpykit.stdlib.io.virtualfileio import *

___ref = IOBase


class IOKit:
    @staticmethod
    def read_exit(io_obj, *args, **kwargs):
        with io_obj:
            return io_obj.read(*args, **kwargs)

    @staticmethod
    def write_exit(io_obj, *args, **kwargs):
        with io_obj:
            return io_obj.write(*args, **kwargs)
