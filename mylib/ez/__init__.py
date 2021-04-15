#!/usr/bin/env python3
"""THIS MODULE MUST ONLY DEPEND ON STANDARD LIBRARIES OR BUILT-IN"""
import ctypes
import functools
import importlib.util
import inspect
import io
import locale

from . import shutil
from . import typing
from .__often_used_imports__ import *

T = typing
path_is_file = os.path.isfile
path_is_dir = os.path.isdir
path_exist = os.path.exists


def __refer_sth():
    return io, shutil


class SingletonMetaClass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class AttrName(metaclass=SingletonMetaClass):
    def __setattr__(self, key, value):
        pass

    def __getattr__(self, item: str) -> str:
        return item


def str_remove_prefix(s: str, prefix: str):
    return s[len(prefix):] if s.startswith(prefix) else s


def str_remove_suffix(s: str, suffix: str):
    return s[:-len(suffix)] if s.endswith(suffix) else s


def get_os_default_lang(*, os_name=os.name):
    if os_name == 'nt':
        win_lang = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale[win_lang]
    else:
        return locale.getdefaultlocale()[0]


def deco_factory_copy_signature(signature_source: T.Callable):
    # https://stackoverflow.com/a/58989918/7966259
    def deco(target: T.Callable):
        @functools.wraps(target)
        def tgt(*args, **kwargs):
            inspect.signature(signature_source).bind(*args, **kwargs)
            return target(*args, **kwargs)

        tgt.__signature__ = inspect.signature(signature_source)
        return tgt

    return deco


class CLIArgumentsList(list):
    merge_option_nargs = True

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.add(*args, **kwargs)

    def add_arg(self, arg):
        if isinstance(arg, str):
            self.append(arg)
        elif isinstance(arg, T.Iterable):
            for a in arg:
                self.add_arg(a)
        else:
            self.append(str(arg))
        return self

    def add_option(self, option_string: str, value):
        if not isinstance(option_string, str):
            raise TypeError('name', str)
        if isinstance(value, str):
            self.append(option_string)
            self.append(value)
        elif isinstance(value, T.Iterable):
            if self.merge_option_nargs:
                self.add(option_string, *value)
            else:
                for v in value:
                    self.add_option(option_string, v)
        elif value is True:
            self.append(option_string)
        elif value is None or value is False:
            pass
        else:
            self.append(option_string)
            self.append(str(value))
        return self

    def add(self, *args, **kwargs):
        for arg in args:
            self.add_arg(arg)
        for k, v in kwargs.items():
            option_string = self.keyword_to_option_string(k)
            self.add_option(option_string, v)
        return self

    @staticmethod
    def keyword_to_option_string(keyword):
        if len(keyword) > 1:
            k = '--' + '-'.join(keyword.split('_'))
        else:
            k = '-' + keyword
        return k


def get_os_default_encoding():
    return locale.getdefaultlocale()[1]


def python_module_from_source_code(
        module_path: str, code_source: str or T.Callable[[str], str], package_path: str = None,
        *, output_file: str = None):
    # How to modify imported source code on-the-fly?
    #     https://stackoverflow.com/a/41863728/7966259  (answered by Martin Valgur)
    # Modules and Packages: Live and Let Die!  (by David Beazley)
    #     http://www.dabeaz.com/modulepackage/ModulePackage.pdf
    #     https://www.youtube.com/watch?v=0oTh1CXRaQ0
    spec = importlib.util.find_spec(module_path, package_path)
    if isinstance(code_source, str):
        source_code = code_source
    elif isinstance(code_source, T.Callable):
        source_code = code_source(spec.loader.get_source(module_path))
    else:
        raise TypeError('code_source', (str, T.Callable[[str], str]))
    if output_file:
        with open(output_file, 'w') as f:
            f.write(source_code)
    module = importlib.util.module_from_spec(spec)
    code_obj = compile(source_code, module.__spec__.origin, 'exec')
    exec(code_obj, module.__dict__)
    sys.modules[module_path] = module
    return module


def python_module_from_filepath(module_name, filepath):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Call:
    target: T.Callable
    args: tuple
    kwargs: dict
    time: T.Optional[float]
    result: T.Any
    exception: T.Optional[Exception]

    def __init__(self, target, *args, **kwargs):
        self.set(target, *args, **kwargs)
        self.clear()

    def clear(self):
        self.time = None
        self.result = None
        self.exception = None

    def set(self, target, *args, **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def get(self):
        self.clear()
        try:
            self.result = self.target(*self.args, **self.kwargs)
            return self.result
        except Exception as e:
            self.exception = e

    def timing_get(self):
        counter = time.perf_counter
        t0 = counter()
        try:
            return self.get()
        finally:
            self.time = counter() - t0


def round_to(x, precision):
    n = len(str(precision).split('.')[-1])
    return round(round(x / precision) * precision, n)


def os_exit_force(*args, **kwargs):
    os._exit(*args, **kwargs)


def thread_factory(group=None, name=None, daemon=None):
    def new_thread(target: T.Callable, *args, **kwargs):
        return threading.Thread(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)

    return new_thread


class ExceptionWithKwargs(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.kwargs = kwargs

    def __str__(self):
        return f"({', '.join([*[str(a) for a in self.args], *[f'{k}={v}' for k, v in self.kwargs.items()]])})"

    def __repr__(self):
        return f'{self.__class__.__name__}{self}'


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


def split_path_dir_base_ext(path, dir_ext=True) -> T.Tuple[str, str, str]:
    """path -> dirname, basename, extension"""
    split = os.path.split
    splitext = os.path.splitext
    p, b = split(path)
    if not dir_ext and os.path.isdir(path):
        n, e = b, ''
    else:
        n, e = splitext(b)
    return p, n, e


def join_path_dir_base_ext(dirname, basename, extension):
    join = os.path.join
    return join(dirname, basename + extension)


def _predicate_fs_path(predication, path):
    os_path_map = {'file': 'isfile', 'dir': 'isdir', 'link': 'islink', 'mount': 'ismount', 'abspath': 'isabs',
                   'abs': 'isabs', 'exist': 'exists', 'f': 'isfile', 'd': 'isdir', 'e': 'exists'}
    return getattr(os.path, os_path_map.get(predication, predication))(path)


@functools.lru_cache()
def predicate_fs_path_cached(predication: str, path):
    return _predicate_fs_path(predication, path)


def predicate_fs_path(predication: str, path, use_cache=False):
    if use_cache:
        return predicate_fs_path_cached(predication, path)
    return _predicate_fs_path(predication, path)


def os_walk_dirs_files(top, topdown=True, onerror=None, followlinks=False):
    join_path = os.path.join
    for root, sub_dirs, sub_files in os.walk(top, topdown=topdown, onerror=onerror, followlinks=followlinks):
        dirs = [join_path(root, bn) for bn in sub_dirs]
        files = [join_path(root, bn) for bn in sub_files]
        yield dirs, files


def glob_dirs_files(pathname, *, recursive=False):
    normpath = os.path.normpath
    is_file = os.path.isfile
    is_dir = os.path.isdir
    gl = glob.glob(pathname, recursive=recursive)
    if not gl:
        return [], []
    try:
        common = os.path.commonpath(gl)
    except ValueError:
        dirs = []
        files = []
        for p in gl:
            if os.path.isfile(p):
                files.append(p)
            elif os.path.isdir(p):
                dirs.append(p)
        return dirs, files
    dirs = []
    files = []
    dirs_set = set()
    files_set = set()
    walk = os_walk_dirs_files(common)
    for p in gl:
        p = normpath(p)
        # print(p, p in files_set or p in dirs_set)
        if p in files_set:
            files.append(p)
            continue
        if p in dirs_set:
            dirs.append(p)
            continue
        for w_dirs, w_files in walk:
            dirs_set.update(w_dirs)
            files_set.update(w_files)
            # print(p, p in files_set or p in dirs_set)
            if p in files_set:
                files.append(p)
                break
            if p in dirs_set:
                dirs.append(p)
                break
        else:
            if is_file(p):
                files_set.add(p)
                files.append(p)
            elif is_dir(p):
                dirs_set.add(p)
                dirs.append(p)
    return dirs, files


def glob_or_exist_dirs_files___alpha(x: T.Union[T.List[str], str, T.NoneType], *,
                                     glob_recurse=False, exist_override_glob=False):
    def glob_then_exist_dirs_files(y):
        _dirs, _files = glob_dirs_files(y, recursive=glob_recurse)
        if _dirs or _files:
            return _dirs, _files
        else:
            if path_is_file(y):
                return [], [y]
            elif path_is_dir(y):
                return [y], []
            else:
                return _dirs, _files

    def exist_then_glob_dirs_files(y):
        if path_is_file(y):
            return [], [y]
        elif path_is_dir(y):
            return [y], []
        else:
            return glob_dirs_files(y, recursive=glob_recurse)

    op = exist_then_glob_dirs_files if exist_override_glob else glob_then_exist_dirs_files

    if isinstance(x, str) or not isinstance(x, T.Iterable):
        return op(x)
    if isinstance(x, T.Iterable):
        dirs = []
        files = []
        for xx in x:
            xx_dirs, xx_files = op(xx)
            dirs.extend(xx_dirs)
            files.extend(xx_files)
        return dirs, files
    raise TypeError('x', (str, T.Iterable[str], 'PathLikeObject'))
