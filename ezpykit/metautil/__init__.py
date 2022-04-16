#!/usr/bin/env python3
import os
from contextlib import contextmanager

from ezpykit.metautil import typing
from ezpykit.metautil.objutil import *
from ezpykit.metautil.singleton import *
from ezpykit.metautil.timer import ctx_ensure_min_time_duration

T = typing


def decofac_add_method_to_class(cls, name=None):
    def deco(func):
        setattr(cls, name or func.__name__, func)
        return func

    return deco


def deco_ctx_with_self(target):
    def tgt(self, *args, **kwargs):
        with self:
            return target(self, *args, **kwargs)

    return tgt


def decofac_ctx(context_obj) -> T.Decorator:
    def deco(target):
        def tgt(*args, **kwargs):
            with context_obj:
                return target(*args, **kwargs)

        return tgt

    return deco


@deco_singleton
class AttrName:
    def __setattr__(self, key, value):
        pass

    def __getattr__(self, item: str) -> str:
        self.__dict__[item] = item
        return item


class ObjectWrapper:
    def __init__(self, obj):
        self.content = obj


class DecoListOfNameMagicVar(list):
    def __call__(self, target):
        self.append(target.__name__)
        return target


def deco_check_arg_type___donotuse(target):
    hint_d = T.get_type_hints(target)

    @wraps(target)
    def tgt(*args, **kwargs):
        arg_d = kwargs.copy()
        arg_d.update(dict(zip(target.__code__.co_varnames, args)))
        for arg_name, arg_value in arg_d.items():
            if arg_name in hint_d:
                hint_type = hint_d.get(arg_name)
                if hint_type.__class__ == T.Union:
                    hint_type = hint_type.__args__
                if not isinstance(arg_value, hint_type):
                    raise TypeError(arg_name, hint_type, arg_value)
        r = target(*args, **kwargs)
        if 'return' in hint_d:
            r_type = type(r)
            hint_type = hint_d['return']
            if r_type != hint_type:
                raise TypeError('return', hint_type, r_type)
        return r

    return tgt


def decofac_check_arg_choice(options: T.Dict[str, T.Iterable], **option_kwargs):
    options.update(option_kwargs)

    def deco(target):
        @wraps(target)
        def tgt(*args, **kwargs):
            arg_d = kwargs.copy()
            arg_d.update(dict(zip(target.__code__.co_varnames, args)))
            for k, v in kwargs:
                if k in options:
                    choices = options[k]
                    if v not in choices:
                        raise ValueError(k, choices, v)
            return target(*args, **kwargs)

        return tgt

    return deco


def install_module(name):
    import os
    if os.system(f'pip install {name}'):
        raise ImportError('failed to install', name)


def hasattr_batch(obj, names):
    return all(map(lambda name: hasattr(obj, name), names))


@contextmanager
def ctx_ensure_module(name, install_name=None):
    from importlib import import_module
    try:
        import_module(name)
        yield
    except ModuleNotFoundError:
        cmd = 'pip install ' + (install_name or name)
        if os.system(cmd):
            raise
        else:
            yield


def is_iterable_but_not_string(x, string_types=(str, bytes, bytearray)):
    return isinstance(x, T.Iterable) and not isinstance(x, string_types)


def sorted_with_equal_groups(_iterable, equal_key=None, sort_key=None, reverse=False):
    sl = sorted(_iterable, key=sort_key, reverse=reverse)
    old_e = sl.pop(0)
    equal_key = equal_key or (lambda x,y: x==y)
    r = [[old_e]]
    for e in sl:
        if not equal_key(e, old_e):
            r.append([])
        r[-1].append(e)
        old_e = e
    return r
