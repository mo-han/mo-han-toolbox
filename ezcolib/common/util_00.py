#!/usr/bin/env python3
def helper_func_do_nothing(*args, **kwargs):
    pass


def deco_factory_add_method_to_class(cls):
    def deco(func):
        setattr(cls, func.__name__, func)
        return func

    return deco
