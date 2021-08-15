#!/usr/bin/env python3
from functools import reduce


def ez_dict_intersection(*dicts):
    return reduce(lambda x, y: dict([(k, v) for k, v in x.items() if (k, v) in y.items()]), dicts)


def ez_dict_union(*dicts):
    r = {}
    for d in dicts:
        r.update(d)
    return r


def ez_dict_difference(x: dict, y: dict):
    return dict([(k, v) for k, v in x.items() if (k, v) not in y.items()])


def ez_dict_multi_get(d: dict, **kwargs):
    return {k: d.get(k, v) for k, v in kwargs.items()}
