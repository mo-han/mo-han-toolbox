#!/usr/bin/env python3
# encoding=utf8

import argparse
import importlib.util
import logging
import sys
from functools import wraps
from typing import Dict, Iterable, Callable, TypeVar

from .math import int_is_power_of_2
from .misc import LOG_FMT, LOG_DTF

_module_data = {}


def limited_argument_choices(choices: Dict[int or str, Iterable] = None) -> Callable:
    """decorator factory: force arguments of a func limited in the given choices

    :param choices: a dict which describes the choices for the value-limited arguments.
            the key of the dict must be either the index of args or the key_str of kwargs,
            while the value of the dict must be an iterable."""
    err_fmt = "value of '{}' is not a valid choice: '{}'"

    def decorator(func):
        if not choices:
            return func

        @wraps(func)
        def decorated_func(*args, **kwargs):
            for i in range(len(args)):
                if i in choices and args[i] not in choices[i]:
                    param_name = func.__code__.co_varnames[i]
                    valid_choices = list(choices[i])
                    raise ValueError(err_fmt.format(param_name, valid_choices))
            for k in kwargs:
                if k in choices and kwargs[k] not in choices[k]:
                    raise ValueError(err_fmt.format(k, list(choices[k])))

            return func(*args, **kwargs)

        return decorated_func

    return decorator


def while_retry_on_exception(max_retries, exceptions, exception_predicate=None, raise_queue=None):
    """decorator factory: force a func re-running for several times on exception(s)"""
    coe = exception_predicate or (lambda e: True)
    max_retries = int(max_retries)
    initial_counter = max_retries if max_retries < 0 else max_retries + 1

    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kwargs):
            cnt = initial_counter
            err = None
            while cnt:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if coe(e):
                        if raise_queue:
                            raise_queue.put(e)
                        err = e
                        cnt -= 1
                        continue
                    else:
                        raise
            else:
                raise err

        return decorated_func

    return decorator


def modify_and_import(module_name, modifier_or_source, package=None):
    # https://stackoverflow.com/a/41863728/7966259
    spec = importlib.util.find_spec(module_name, package)
    if isinstance(modifier_or_source, str):
        source = modifier_or_source
    else:
        source = modifier_or_source(spec.loader.get_source(module_name))
    module = importlib.util.module_from_spec(spec)
    code_obj = compile(source, module.__spec__.origin, 'exec')
    exec(code_obj, module.__dict__)
    sys.modules[module_name] = module
    return module


def singleton(cls):
    _instances = {}

    def get_instance():
        if cls not in _instances:
            _instances[cls] = cls()
        return _instances[cls]

    return get_instance


class VoidDuck:
    """a void, versatile, useless and quiet duck, called in any way, return nothing, raise nothing"""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False


def str_ishex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def arg_type_pow2(x):
    i = int(x)
    if int_is_power_of_2(i):
        return i
    else:
        raise argparse.ArgumentTypeError("'{}' is not power of 2".format(x))


def arg_type_range_factory(x_type, x_range_condition: str):
    def arg_type_range(x):
        xx = x_type(x)
        if eval(x_range_condition):
            return xx
        else:
            raise argparse.ArgumentTypeError("'{}' not in range {}".format(x, x_range_condition))

    return arg_type_range


def new_logger(logger_name: str, level: str = 'INFO', fmt=LOG_FMT, datetime_fmt=LOG_DTF, handlers_l: list = None):
    formatter = logging.Formatter(fmt=fmt, datefmt=datetime_fmt)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    if not handlers_l:
        handlers_l = [logging.StreamHandler()]
    for h in handlers_l:
        h.setFormatter(formatter)
        logger.addHandler(h)
    return logger


class ArgumentParserCompactOptionHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            # noinspection PyProtectedMember
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(action.option_strings) + ' ' + args_string


def import_pywinauto():
    """sys.coinit_flags=2 before import pywinauto
    https://github.com/pywinauto/pywinauto/issues/472"""
    sys.coinit_flags = 2
    import pywinauto
    return pywinauto


def with_self_context(func):
    """decorator: wrap a class method inside a `with self: ...` context"""

    def decorated_func(self, *args, **kwargs):
        with self:
            r = func(self, *args, **kwargs)
        return r

    return decorated_func