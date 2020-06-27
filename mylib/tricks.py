#!/usr/bin/env python3
# encoding=utf8

import argparse
import importlib.util
import logging
import sys
from functools import wraps
from typing import Dict, Iterable, Callable

from .math import int_is_power_of_2
from .misc import LOG_FMT, LOG_DTF

_module_data = {}

Decorator = Callable[[Callable], Callable]


class TypedQueue:
    def put(self, *args, **kwargs):
        ...

    def get(self, *args, **kwargs):
        ...


def limit_argv_choice(choices: Dict[int or str, Iterable] = None) -> Decorator:
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


def loop_retry_on_exception(exceptions: Exception or Iterable[Exception], max_retries: int = 3,
                            exception_tester=Callable[[Exception], bool], exception_queue=TypedQueue) -> Decorator:
    """decorator factory: force a func re-running for several times on exception(s)"""
    test_exc = exception_tester or (lambda e: True)
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
                    if test_exc(e):
                        if exception_queue:
                            exception_queue.put(e)
                        err = e
                        cnt -= 1
                        continue
                    else:
                        raise
            else:
                raise err

        return decorated_func

    return decorator


def modify_and_import(module_path: str, code_modifier: str or Callable, package_path: str = None):
    # How to modify imported source code on-the-fly?
    #     https://stackoverflow.com/a/41863728/7966259  (answered by Martin Valgur)
    # Modules and Packages: Live and Let Die!  (by David Beazley)
    #     http://www.dabeaz.com/modulepackage/ModulePackage.pdf
    #     https://www.youtube.com/watch?v=0oTh1CXRaQ0
    spec = importlib.util.find_spec(module_path, package_path)
    if isinstance(code_modifier, str):
        source = code_modifier
    else:
        source = code_modifier(spec.loader.get_source(module_path))
    module = importlib.util.module_from_spec(spec)
    code_obj = compile(source, module.__spec__.origin, 'exec')
    exec(code_obj, module.__dict__)
    sys.modules[module_path] = module
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


def getitem_default(x, index_or_key, default=None):
    try:
        return x[index_or_key]
    except (IndexError, KeyError):
        return default


def getitem_set_default(x, index_or_key, default=None):
    try:
        return x[index_or_key]
    except IndexError:
        x += type(x)([default] * (index_or_key - len(x)))
        return default
    except KeyError:
        x[index_or_key] = default
        return default


def remove_from_iterable(source: Iterable, remove: Iterable) -> list:
    return [x for x in source if x not in remove]
