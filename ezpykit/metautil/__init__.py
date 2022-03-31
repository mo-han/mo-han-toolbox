#!/usr/bin/env python3
import os
from functools import wraps
from contextlib import contextmanager

from ezpykit.metautil import typing
from ezpykit.metautil.singleton import deco_singleton, SingletonMetaClass
from ezpykit.metautil.timer import ctx_minimum_duration

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


class VoidDuck:
    """a void, versatile, useless and quiet duck, call in any way, return nothing, raise nothing"""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False


def hasattr_batch(obj, names):
    return all(map(lambda name: hasattr(obj, name), names))


@contextmanager
def ctx_ensure_module(name, pkg_name=None):
    from importlib import import_module
    try:
        import_module(name)
    except ModuleNotFoundError:
        cmd = 'pip install ' + (pkg_name or name)
        if os.system(cmd):
            raise
    else:
        yield
