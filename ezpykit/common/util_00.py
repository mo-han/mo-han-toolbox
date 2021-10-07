#!/usr/bin/env python3
from mylib.easy import T


def helper_func_do_nothing(*args, **kwargs):
    pass


def deco_factory_add_method_to_class(cls):
    def deco(func):
        setattr(cls, func.__name__, func)
        return func

    return deco


class SingletonMetaClass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def deco_inside_ctx_method_self(target):
    """decorator: wrap a class method inside a `with self: ...` context"""

    def tgt(self, *args, **kwargs):
        with self:
            return target(self, *args, **kwargs)

    return tgt


def deco_factory_ctx(context_obj) -> T.Decorator:
    def deco(target):
        def tgt(*args, **kwargs):
            with context_obj:
                return target(*args, **kwargs)

        return tgt

    return deco
