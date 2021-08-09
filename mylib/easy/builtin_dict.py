#!/usr/bin/env python3
from functools import reduce


def dict_intersection(*dicts):
    return reduce(lambda x, y: dict([(k, v) for k, v in x.items() if (k, v) in y.items()]), dicts)


def dict_union___unstable(*dicts):
    return reduce(lambda x, y: dict(x.items() | y.items()), dicts)


def dict_union(*dicts):
    r = {}
    for d in dicts:
        r.update(d)
    return r


def dict_difference(x: dict, y: dict):
    return dict([(k, v) for k, v in x.items() if (k, v) not in y.items()])


def dict_symmetric_difference___unstable(*dicts):
    return reduce(lambda x, y: dict(x.items() ^ y.items()), dicts)


class Dict(dict):
    def __call__(self, *args, **kwargs):
        if args and kwargs:
            d = {}
            for k in args:
                if k in self:
                    d[k] = self[k]
            for k, v in kwargs.items():
                d[k] = self.get(k, v)
            return d
        elif args:
            return [self[k] for k in args if k in self]
        elif kwargs:
            return {k: self.get(k, v) for k, v in kwargs.items()}
