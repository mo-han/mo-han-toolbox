#!/usr/bin/env python3
# encoding=utf8

import argparse
import importlib.util
import logging
import sys
from functools import wraps
from .math import int_is_power_of_2
from .misc import LOG_FMT, LOG_DTF

_module_data = {}


def retry_on_exception(max_retries, exceptions, condition_on_exceptions=None, raise_queue=None):
    coe = condition_on_exceptions or (lambda e: True)
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
