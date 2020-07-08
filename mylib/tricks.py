#!/usr/bin/env python3
# encoding=utf8

import argparse
import importlib.util
import logging
import sys
from collections import defaultdict
from functools import wraps
from typing import Dict, Iterable, Callable

from .misc import LOG_FMT, LOG_DTF
from .number import int_is_power_of_2

_module_data = {}

Decorator = Callable[[Callable], Callable]


class TypingQueue:
    def put(self, *args, **kwargs):
        ...

    def get(self, *args, **kwargs):
        ...


def limit_argv_choice(choices: Dict[int or str, Iterable]) -> Decorator:
    """decorator factory: force arguments of a func limited in the given choices

    :param choices: a dict which describes the choices for the value-limited arguments.
            the key of the dict must be either the index of args or the key_str of kwargs,
            while the value of the dict must be an iterable."""
    err_fmt = "value of '{}' is not a valid choice: '{}'"

    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kwargs):
            for i in range(len(args)):
                if i in choices and args[i] not in choices[i]:
                    param_name = func.__code__.co_varnames[i]
                    raise ValueError(err_fmt.format(param_name, set(choices[i])))
            for k in kwargs:
                if k in choices and kwargs[k] not in choices[k]:
                    raise ValueError(err_fmt.format(k, set(choices[k])))

            return func(*args, **kwargs)

        return decorated_func

    return decorator


def with_exception_retry(exceptions: Exception or Iterable[Exception], max_retries: int = 3,
                         enable_default=False, default=None,
                         exception_predicate: Callable[[Exception], bool] = None,
                         exception_queue: TypingQueue = None) -> Decorator:
    """decorator factory: force a func re-running for several times on exception(s)"""
    predicate = exception_predicate or (lambda e: True)
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
                    if predicate(e):
                        if exception_queue:
                            exception_queue.put(e)
                        err = e
                        cnt -= 1
                        continue
                    else:
                        if enable_default:
                            return default
                        raise
            else:
                if enable_default:
                    return default
                raise err

        return decorated_func

    return decorator


def modify_and_import(module_path: str, code_modifier: str or Callable, package_path: str = None,
                      output: bool = False, output_file: str = 'tmp.py'):
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
    if output:
        with open(output_file, 'w') as f:
            f.write(source)
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


def get_logger(logger_name: str, level: str = 'INFO', fmt=LOG_FMT, datetime_fmt=LOG_DTF, handlers_l: list = None):
    formatter = logging.Formatter(fmt=fmt, datefmt=datetime_fmt)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    if not handlers_l:
        handlers_l = [logging.StreamHandler()]
    for h in handlers_l:
        h.setFormatter(formatter)
        logger.addHandler(h)
    return logger


class ArgParseCompactHelpFormatter(argparse.HelpFormatter):
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


def remove_from_list(source: Iterable, rmv_set: Iterable) -> list:
    """return a list, which contains elements in source but not in rmv_set"""
    return [x for x in source if x not in rmv_set]


def dedup_list(source: Iterable) -> list:
    r = []
    [r.append(e) for e in source if e not in r]
    return r


def constrain_value(x, x_type: Callable, x_constraint: str or Callable = None, enable_default=False, default=None):
    x = x_type(x)
    if x_constraint:
        if isinstance(x_constraint, str) and eval(x_constraint):
            return x
        elif isinstance(x_constraint, Callable) and x_constraint(x):
            return x
        elif enable_default:
            return default
        else:
            raise ValueError("'{}' conflicts with '{}'".format(x, x_constraint))
    else:
        return x


def get_kwargs(**kwargs):
    return kwargs


def default_dict_tree():
    return defaultdict(default_dict_tree)


class AttrTree:
    __wrapped__ = None

    def __init__(self, data: dict = None, **kwargs):
        if data:
            self.__dict__.update(data)
        if kwargs:
            self.__dict__.update(kwargs)

    def __getitem__(self, item):
        try:
            return self.__dict__[item]
        except KeyError:
            v = self.__dict__[item] = AttrTree()
        return v

    __getattr__ = __getitem__

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    __setattr__ = __setitem__

    def __delitem__(self, key):
        del self.__dict__[key]

    __delattr__ = __delitem__

    def __iter__(self):
        yield from self.__dict__

    def __contains__(self, item):
        return item in self.__dict__

    @property
    def __data__(self):
        tmp = {}
        for k in self.__dict__:
            if isinstance(self[k], AttrTree):
                tmp[k] = self[k].__data__
            else:
                tmp[k] = self[k]
        return tmp

    def __bool__(self):
        return bool(self.__dict__)

    def __len__(self):
        return len(self.__dict__)
