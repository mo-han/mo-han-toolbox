#!/usr/bin/env python3
from glob import *


def iglob_chain(*pattern, **kwargs):
    import itertools
    return itertools.chain.from_iterable(glob(p, **kwargs) for p in pattern)
