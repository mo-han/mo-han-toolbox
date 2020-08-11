#!/usr/bin/env python3
# encoding=utf8

import argparse
import hashlib
import importlib.util
import logging
import sys
from collections import defaultdict
from functools import wraps
from typing import Dict, Iterable, Callable, Generator, Tuple, Union, Mapping, List

from .misc import LOG_FMT, LOG_DTF
from .number import int_is_power_of_2

Decorator = Callable[[Callable], Callable]


class QueueType:
    def put(self, *args, **kwargs):
        ...

    def get(self, *args, **kwargs):
        ...


JSONType = Union[str, int, float, bool, None, Mapping[str, 'JSON'], List['JSON']]


def range_from_expr(expr: str) -> Generator:
    sections = [[int(n.strip() or 1) for n in e.split('-')] for e in expr.split(',')]
    for s in sections:
        yield from range(s[0], s[-1] + 1)


def decorator_factory_args_choices(choices: Dict[int or str, Iterable]) -> Decorator:
    """decorator factory: force arguments of a func limited inside the given choices

    :param choices: a dict which describes the choices of arguments
        the key of the dict must be either the index of args or the key(str) of kwargs
        the value of the dict must be an iterable."""
    err_fmt = "value of '{}' is not a valid choice in {}"

    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kwargs):
            for arg_index in range(len(args)):
                param_name = func.__code__.co_varnames[arg_index]
                if arg_index in choices and args[arg_index] not in choices[arg_index]:
                    raise ValueError(err_fmt.format(param_name, choices[arg_index]))
                elif param_name in choices and args[arg_index] not in choices[param_name]:
                    raise ValueError(err_fmt.format(param_name, choices[param_name]))
            for param_name in kwargs:
                if param_name in choices and kwargs[param_name] not in choices[param_name]:
                    raise ValueError(err_fmt.format(param_name, choices[param_name]))

            return func(*args, **kwargs)

        return decorated_func

    return decorator


def context_exception_retry(exceptions: Exception or Iterable[Exception], max_retries: int = 3,
                            enable_default=False, default=None,
                            exception_predicate: Callable[[Exception], bool] = None,
                            exception_queue: QueueType = None) -> Decorator:
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
        return ', '.join(action.option_strings) + '  ' + args_string


def decorator_self_context(func):
    """decorator: wrap a class method inside a `with self: ...` context"""

    def decorated_func(self, *args, **kwargs):
        with self:
            return func(self, *args, **kwargs)

    return decorated_func


def decorator_factory_with_context(context_obj) -> Decorator:
    def decorator_with_context(func):
        def decorated_func(*args, **kwargs):
            with context_obj:
                return func(*args, **kwargs)

        return decorated_func

    return decorator_with_context


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


class Attreebute:
    """Attribute Tree"""
    __exclude__ = ['__data__', '__index__']

    def __init__(self, tree_data: dict = None, json_filepath: str = None, **kwargs):
        self.__data__ = {}
        if tree_data:
            self.__from_dict__(tree_data)
        if json_filepath:
            self.__from_json__(json_filepath)
        if kwargs:
            self.__from_dict__(kwargs)

    def __from_dict__(self, tree_data: dict):
        for k, v in tree_data.items():
            if isinstance(v, dict):
                self.__dict__[k] = Attreebute(tree_data=v)
            else:
                self.__dict__[k] = v
            self.__update_data__(k, self[k])

    def __from_json__(self, json_filepath: str):
        from mylib.os_util import read_json_file
        self.__from_dict__(read_json_file(json_filepath))

    def __to_dict__(self):
        return self.__data__

    def __to_json__(self, json_filepath: str):
        from mylib.os_util import write_json_file
        write_json_file(json_filepath, self.__data__, indent=4)

    def __query__(self, *args, **kwargs):
        if not args and not kwargs:
            return self.__table__

    __call__ = __query__

    def __update_data__(self, key, value):
        if isinstance(value, Attreebute):
            self.__data__[key] = value.__data__
        elif key not in self.__exclude__:
            self.__data__[key] = value

    @property
    def __map__(self):
        tmp = {}
        for k in self.__dict__:
            v = self[k]
            if isinstance(v, Attreebute):
                for vk in v.__map__:
                    tmp['{}.{}'.format(k, vk)] = v.__map__[vk]
            elif k not in self.__exclude__:
                tmp[k] = v
        return tmp

    @property
    def __table__(self):
        return sorted(self.__map__.items())

    @staticmethod
    def __valid_path__(path):
        if '.' in str(path):
            key, sub_path = path.split('.', maxsplit=1)
        else:
            key, sub_path = path, None
        return key, sub_path

    def __getitem__(self, item):
        key, sub_path = self.__valid_path__(item)
        try:
            target = self.__dict__[key]
        except KeyError:
            target = self.__dict__[key] = Attreebute()
            self.__update_data__(key, target)
        if sub_path:
            return target[sub_path]
        else:
            return target

    __getattr__ = __getitem__

    def __setitem__(self, key, value):
        self_key, sub_path = self.__valid_path__(key)
        if sub_path:
            if self_key in self:
                self[self_key][sub_path] = value
            else:
                target = self.__dict__[self_key] = Attreebute()
                self.__update_data__(self_key, target)
                target[sub_path] = value
        else:
            self.__dict__[self_key] = value
            self.__update_data__(self_key, value)

    __setattr__ = __setitem__

    def __delitem__(self, key):
        self_key, sub_path = self.__valid_path__(key)
        if sub_path:
            del self.__dict__[self_key][sub_path]
        else:
            del self.__dict__[self_key]
            del self.__data__[self_key]

    def __delattr__(self, item):
        try:
            self.__delitem__(item)
        except KeyError as e:
            raise AttributeError(*e.args)

    def __iter__(self):
        yield from self.__dict__

    def __contains__(self, item):
        return item in self.__dict__

    def __bool__(self):
        return bool(self.__data__)

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        table = self.__table__
        half = len(table) // 2
        head_end, mid_begin, mid_end, tail_begin = 6, half - 3, half + 3, -6
        max_ = 3 * (6 + 1)
        lines = [super(Attreebute, self).__repr__()]
        if len(table) >= max_:
            lines.extend(['{}={}'.format(k, v) for k, v in table[:head_end]])
            lines.append('...')
            lines.extend(['{}={}'.format(k, v) for k, v in table[mid_begin:mid_end]])
            lines.append('...')
            lines.extend(['{}={}'.format(k, v) for k, v in table[tail_begin:]])
        else:
            lines.extend(['{}={}'.format(k, v) for k, v in table])
        return '\n'.join(lines)

    def __str__(self):
        return '\n'.join(['{}={}'.format(k, v) for k, v in self.__table__])


def until_return_try(schedule: Iterable[dict], unified_exception=Exception):
    """try through `schedule`, bypass specified exception, until sth returned, then return it.
    format of every task inside `schedule`:
        {'callable':..., 'args':(...), 'kwargs':{...}, 'exception':...}
    if a task in `schedule` has `exception` specified for its own, the `unified_exception` will be ignored
    if a task has wrong format, it will be ignored"""
    for task in schedule:
        if 'exception' in task:
            exception = task['exception']
        else:
            exception = unified_exception
        if 'args' in task:
            args = task['args']
        else:
            args = ()
        if 'kwargs' in task:
            kwargs = task['kwargs']
        else:
            kwargs = {}
        try:
            return task['callable'](*args, **kwargs)
        except exception:
            pass


def hex_hash(data: bytes, algorithm: str = 'md5') -> str:
    return getattr(hashlib, algorithm.replace('-', '_'))(data).hexdigest()


def get_args_kwargs(*args, **kwargs) -> Tuple[list, dict]:
    return list(args), kwargs


class WrappedList(list):
    pass


def seconds_from_colon_time(t: str) -> float:
    def greater_0(x):
        return x >= 0

    def less_60(x):
        return x < 60

    def less_24(x):
        return x < 24

    t_value_error = ValueError(t)
    parts = t.split(':')
    last = parts[-1]
    before_last = parts[:-1]
    after_1st = parts[1:]
    after_2nd = parts[2:]
    n = len(parts)

    if 4 < n < 1:
        raise t_value_error
    try:
        float(last)
        [int(p) for p in before_last]
    except ValueError:
        raise t_value_error
    if not all([greater_0(float(x)) for x in after_1st]):
        raise t_value_error
    sign = -1 if t.startswith('-') else 1

    if n == 1:
        total = float(t)
    elif n == 4:
        if not all([less_60(float(x)) for x in after_2nd]):
            raise t_value_error
        d, h, m = [abs(int(x)) for x in before_last]
        if not less_24(h):
            raise t_value_error
        s = float(last)
        total = (d * 24 + h) * 3600 + m * 60 + s
    else:
        if not all([less_60(float(x)) for x in after_1st]):
            raise t_value_error
        total = 0
        for x in parts:
            total = total * 60 + abs(float(x))

    return total if total == 0 else total * sign
