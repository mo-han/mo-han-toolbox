#!/usr/bin/env python3
from functools import reduce


def dict_intersection(dicts):
    return reduce(lambda x, y: dict([(k, v) for k, v in x.items() if (k, v) in y.items()]), dicts)


def dict_union___unstable(dicts):
    return reduce(lambda x, y: dict(x.items() | y.items()), dicts)


def dict_difference(x: dict, y: dict):
    return dict([(k, v) for k, v in x.items() if (k, v) not in y.items()])


def dict_symmetric_difference___unstable(dicts):
    return reduce(lambda x, y: dict(x.items() ^ y.items()), dicts)
