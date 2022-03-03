#!/usr/bin/env python3
from functools import wraps

from ezpykit.allinone.singleton import deco_singleton
from ezpykit.enhance_stdlib import typing as T


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
