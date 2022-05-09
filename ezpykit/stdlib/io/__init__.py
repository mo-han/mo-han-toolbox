#!/usr/bin/env python3
from io import *
from ezpykit.metautil import T

from ezpykit.stdlib.io.slicefileio import *
from ezpykit.stdlib.io.virtualfileio import *

___ref = IOBase


class IOKit:
    @staticmethod
    def read_exit(io_obj, *args, **kwargs) -> T.Union[str, bytes]:
        with io_obj:
            return io_obj.read(*args, **kwargs)

    @staticmethod
    def write_exit(io_obj, x, *args, **kwargs):
        with io_obj:
            return io_obj.write(x, *args, **kwargs)

    @staticmethod
    def open(fp, *args, open_with=True, **kwargs):
        if isinstance(open_with, str):
            return open(fp, *args, encoding=open_with, **kwargs)
        elif isinstance(open_with, tuple):
            mode, enc = open_with
            return open(fp, mode, *args, encoding=enc, **kwargs)
        elif isinstance(open_with, dict):
            return open(fp, *args, **open_with, **kwargs)
        else:
            return open(fp, *args, **kwargs)
