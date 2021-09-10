#!/usr/bin/env python3
import contextlib as contextlib
import ctypes as ctypes
import functools as functools
import importlib as importlib
import importlib.util
import inspect as inspect
import locale as locale
import urllib as urllib
import urllib.parse

from . import io
from . import shutil
from .__common__ import *
from .extra import *
from .stdlibs.threading import *

REGEX_HEX_CHAR = '[0-9a-fA-F]'
REGEX_GUID = '-'.join([f'{REGEX_HEX_CHAR}{{{__i}}}' for __i in (8, 4, 4, 4, 12)])


def __refer_sth():
    return io, shutil, contextlib


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
        self.__dict__[item] = item
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
    merge_option_nargs = False

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
            option_string = self._spec_convert_keyword_to_option_name(k)
            self.add_option(option_string, v)
        return self

    @staticmethod
    def _spec_convert_keyword_to_option_name(keyword):
        if len(keyword) > 1:
            opt_name = '--' + '-'.join(keyword.split('_'))
        else:
            opt_name = '-' + keyword
        return opt_name


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


def round_to(x, precision):
    n = len(str(precision).split('.')[-1])
    return round(round(x / precision) * precision, n)


def os_exit_force(*args, **kwargs):
    os._exit(*args, **kwargs)


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


def walk_to_dirs_files(top, topdown=True, onerror=None, followlinks=False):
    join_path = os.path.join
    for root, sub_dirs, sub_files in os.walk(top, topdown=topdown, onerror=onerror, followlinks=followlinks):
        dirs = [join_path(root, bn) for bn in sub_dirs]
        files = [join_path(root, bn) for bn in sub_files]
        yield dirs, files


def glob_to_dirs_files(pathname, *, recursive=False):
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
    walk = walk_to_dirs_files(common)
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


def glob_then_exist_to_dirs_files(x: str, glob_recurse=False):
    _dirs, _files = glob_to_dirs_files(x, recursive=glob_recurse)
    if _dirs or _files:
        return _dirs, _files
    else:
        if path_is_file(x):
            return [], [x]
        elif path_is_dir(x):
            return [x], []
        else:
            return _dirs, _files


def exist_then_glob_to_dirs_files(x: str, glob_recurse=False):
    if path_is_file(x):
        return [], [x]
    elif path_is_dir(x):
        return [x], []
    else:
        return glob_to_dirs_files(x, recursive=glob_recurse)


def glob_or_exist_to_dirs_files(x: T.Union[T.Iterable[str], str, T.NoneType], *,
                                glob_recurse=False, exist_prior_to_glob=False):
    if exist_prior_to_glob:
        get_dirs_files = functools.partial(exist_then_glob_to_dirs_files, glob_recurse=glob_recurse)
    else:
        get_dirs_files = functools.partial(glob_then_exist_to_dirs_files, glob_recurse=glob_recurse)

    if isinstance(x, str) or not isinstance(x, T.Iterable):
        return get_dirs_files(x)
    if isinstance(x, T.Iterable):
        dirs = []
        files = []
        for xx in x:
            xx_dirs, xx_files = get_dirs_files(xx)
            dirs.extend(xx_dirs)
            files.extend(xx_files)
        return dirs, files
    raise TypeError('x', (str, T.Iterable[str], 'PathLikeObject'))


def deco_factory_param_value_choices(choices: T.Dict[int or str, T.Iterable] or None, *args,
                                     **kwargs) -> T.Decorator:
    """decorator factory: force arguments of a func limited inside the given choices

    :param choices: a dict which describes the choices of arguments
        the key of the dict must be either the index of args or the key(str) of kwargs
        the value of the dict must be an iterable
        choices could be supplemented by *args and **kwargs
        choices could be empty or None"""
    choices = choices or {}
    for i in range(len(args)):
        choices[i] = args[i]
    choices.update(kwargs)
    err_fmt = "argument {}={} is not valid, choose from {})"

    def deco(target):
        @functools.wraps(target)
        def wrapped_target(*target_args, **target_kwargs):
            for arg_index in range(len(target_args)):
                param_name = target.__code__.co_varnames[arg_index]
                value = target_args[arg_index]
                if arg_index in choices and value not in choices[arg_index]:
                    raise ValueError(err_fmt.format(param_name, choices[arg_index]))
                elif param_name in choices and value not in choices[param_name]:
                    raise ValueError(err_fmt.format(param_name, value, choices[param_name]))
            for param_name in target_kwargs:
                value = target_kwargs[param_name]
                if param_name in choices and value not in choices[param_name]:
                    raise ValueError(err_fmt.format(param_name, value, choices[param_name]))

            return target(*target_args, **target_kwargs)

        return wrapped_target

    return deco


def dedup_list(source: T.Iterable) -> list:
    r = []
    [r.append(e) for e in source if e not in r]
    return r


def deco_cached_call(target):
    cache = {}

    @functools.wraps(target)
    def deco(*args, **kwargs):
        cache_key = target
        if args:
            cache_key = cache_key, str(args)
        if kwargs:
            cache_key = *cache_key, str(kwargs)
        try:
            return cache[cache_key]
        except KeyError:
            r = target(*args, **kwargs)
            cache[cache_key] = r
            return r

    return deco


class AttrConstEllipsisForStringMetaClass(type):
    def __new__(mcs, name, bases, namespace):
        return super().__new__(mcs, name, bases, {k: k if v is ... else v for k, v in namespace.items()})


class PipePair:
    def __init__(self, text_mode=False, **kwargs):
        r, w = os.pipe()
        self.r = self.readable_pipe = os.fdopen(r, 'r' if text_mode else 'rb', **kwargs)
        self.w = self.writable_pipe = os.fdopen(w, 'w' if text_mode else 'wb', **kwargs)
        self.r_w_pair = (self.r, self.w)


class ByteStreamBufferedReaderScraperPreAlpha:
    def __init__(self, stream: T.Union[io.BufferedReader, T.BinaryIO], timeout=None,
                 relay_to=None, scrape_to_bytearray=True, scrape_to_pipe=False):
        self.stream = stream
        self._inactive_event = threading.Event()

        if timeout is None:
            self.stream_peek = stream.peek
            self.stream_read = stream.read
        else:
            self.stream_peek = ACall(stream.peek).set_timeout(timeout).get_result_timeout
            self.stream_read = ACall(stream.read).set_timeout(timeout).get_result_timeout

        if relay_to:
            self.relay = self._relay
            if isinstance(relay_to, io.TextIOWrapper):
                relay_to = relay_to.buffer
            if isinstance(relay_to, io.BufferedWriter):
                self._relay_dst = relay_to
            else:
                raise TypeError('relay_to', io.BufferedWriter)
        else:
            self.relay = self._pass

        if scrape_to_bytearray:
            self.bytearray = bytearray()
            self.bytearray_lock = threading.Lock()
            self.write_bytearray = self._write_bytearray
            self.read_bytearray = self._read_bytearray
            self.peek_bytearray = self._peek_bytearray
        else:
            self.write_bytearray = self._pass

        if scrape_to_pipe:
            r, w = PipePair(text_mode=False).r_w_pair
            r: io.BufferedReader
            self.write_pipe = w.write
            self.flush_pipe = w.flush
            self.close_pipe = w.close
            self.read_pipe = r.read
            self.peek_pipe = r.peek
        else:
            self.write_pipe = self._pass
            self.flush_pipe = self._pass
            self.close_pipe = self._pass

    @staticmethod
    def _pass(*args):
        pass

    def _relay(self, b):
        self._relay_dst.write(b)
        self._relay_dst.flush()

    @property
    def is_inactive(self):
        return self._inactive_event.wait(0)

    def wait_inactive(self, timeout=None):
        return self._inactive_event.wait(timeout)

    def set_inactive(self):
        self._inactive_event.set()
        self.close_pipe()

    def start_scape(self):
        ez_thread_factory(daemon=True)(self.scrape).start()
        return self

    def scrape(self):
        while 1:
            try:
                peek = self.stream_peek()
            except TimeoutError:
                self.set_inactive()
                break
            else:
                n = len(peek)
                if n:
                    read = self.stream_read(n)
                    self.relay(read)
                    self.write_bytearray(read)
                    self.write_pipe(read)
                    self.flush_pipe()
                else:
                    self.set_inactive()
                    break

    def _write_bytearray(self, b):
        self.bytearray_lock.acquire()
        self.bytearray.extend(b)
        self.bytearray_lock.release()
        return self

    def _read_bytearray(self, size=-1) -> bytearray:
        self.bytearray_lock.acquire()
        b = self.bytearray[:size]
        if size == -1 or size == len(self.bytearray):
            self.bytearray.clear()
        else:
            self.bytearray[:] = self.bytearray[size:]
        self.bytearray_lock.release()
        return b

    def _peek_bytearray(self, size=-1) -> bytearray:
        self.bytearray_lock.acquire()
        b = self.bytearray[:size]
        self.bytearray_lock.release()
        return b


class SubProcessBytePipeTranscriberPreAlpha:

    def __init__(self, p: subprocess.Popen, pipe_timeout=None, to_pipe=False, to_bytearray=True):
        if not isinstance(p.stdout, io.BufferedReader) or not isinstance(p.stderr, io.BufferedReader):
            raise ValueError('`p` must have both `stdout` and `stderr` as `io.BufferedReader`')
        self.p = p
        self.o = ByteStreamBufferedReaderScraperPreAlpha(p.stdout, timeout=pipe_timeout, relay_to=sys.stdout,
                                                         scrape_to_bytearray=to_bytearray, scrape_to_pipe=to_pipe)
        self.e = ByteStreamBufferedReaderScraperPreAlpha(p.stderr, timeout=pipe_timeout, relay_to=sys.stderr,
                                                         scrape_to_bytearray=to_bytearray, scrape_to_pipe=to_pipe)
        self._all_pipe_scrapers_inactive_barrier = threading.Barrier(3)
        self._all_pipe_scrapers_inactive_event = threading.Event()
        ez_thread_factory(daemon=True)(self._wait_pipe_scraper_inactive, self.o).start()
        ez_thread_factory(daemon=True)(self._wait_pipe_scraper_inactive, self.e).start()

    @property
    def is_complete(self):
        return self.p.poll() is not None

    @property
    def is_inactive(self):
        return self.wait_inactive()

    def wait_inactive(self):
        if self._all_pipe_scrapers_inactive_event.wait(0):
            return True
        self._all_pipe_scrapers_inactive_barrier.wait()
        self._all_pipe_scrapers_inactive_event.set()
        return self.wait_inactive()

    def _wait_pipe_scraper_inactive(self, x: ByteStreamBufferedReaderScraperPreAlpha):
        x.wait_inactive()
        self._all_pipe_scrapers_inactive_barrier.wait()

    def start(self):
        self.o.start_scape()
        self.e.start_scape()

    def wait_complete(self):
        self.wait_inactive()
        return self.p.wait()


class REMatchWrapper:
    def __init__(self, match_obj):
        self.match = match_obj

    @property
    def group0(self):
        m = self.match
        return m.group(0) if m else None

    def groups(self, default=None):
        m = self.match
        return m.groups(default=default) if m else tuple()

    def group_dict(self, default=None):
        m = self.match
        return m.groupdict(default=default) if m else dict()


def call_factory_retry(target, max_retries: int = 3, exceptions=Exception,
                       enable_default=False, default=None,
                       exception_predicate: T.Callable[[Exception], bool] = None,
                       exception_handler: T.Callable[[Exception], T.Any] = None):
    exceptions = exceptions or ()
    predicate = exception_predicate or (lambda e: True)
    handle = exception_handler or (lambda e: None)
    max_retries = int(max_retries)
    initial_counter = max_retries if max_retries < 0 else max_retries + 1

    @deco_factory_copy_signature(target)
    def tgt(*args, **kwargs):
        cnt = initial_counter
        err = None
        while cnt:
            try:
                return target(*args, **kwargs)
            except exceptions as e:
                if predicate(e):
                    handle(e)
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

    return tgt


def deco_factory_retry(max_retries: int = 3, exceptions=Exception,
                       enable_default=False, default=None,
                       exception_predicate: T.Callable[[Exception], bool] = None,
                       exception_handler: T.Callable[[Exception], T.Any] = None) -> T.Decorator:
    def _call_target_retry(target):
        return call_factory_retry(target, max_retries=max_retries, exceptions=exceptions,
                                  enable_default=enable_default, default=default,
                                  exception_predicate=exception_predicate, exception_handler=exception_handler)

    def deco(target):
        return _call_target_retry(target)

    return deco


class FirstCountLastStop:
    def __init__(self):
        self.first = 0
        self.total = 0
        self.last = 0
        self.stop = 1

    def set_first_and_total(self, first, count):
        self.first = first
        self.total = count
        self.stop = first + count
        self.last = self.stop - 1
        return self


class EzTypeError(TypeError):
    def __init__(self, name, *args, expect=None, given=None):
        super(EzTypeError, self).__init__(name, *args)
        if expect:
            self.expect = expect
        if given:
            self.given = given

    @property
    def has_expect(self):
        return hasattr(self, 'expect')

    @property
    def has_given(self):
        return hasattr(self, 'given')


def find_most_frequent_in_iterable(x):
    count = {}
    for i in x:
        count[i] = count.get(i, 0) + 1
    if not count:
        return []
    the_max = max(count.values())
    return [k for k, v in count.items() if v == the_max]


class Timer:
    def __init__(self, n=1):
        self.n = n
        self.reset()

    def __enter__(self):
        self.t0 = time.perf_counter()
        self.duration = 0
        self.records = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = self.elapse()

    def start(self):
        return self.__enter__()

    def stop(self):
        self.__exit__(None, None, None)
        return self

    def reset(self):
        return self.__enter__()

    def range(self):
        return range(self.n)

    @property
    def average(self):
        return self.duration / self.n

    def record(self):
        t = self.elapse()
        self.records.append(t)
        return t

    def elapse(self):
        return time.perf_counter() - self.t0


def ez_parse_netloc(url: str):
    urlparse = urllib.parse.urlparse
    p = urlparse(url)
    if not p.scheme and not p.netloc:
        p = urlparse('scheme://' + url)
    return p


def ez_named_tuple_replace(named_tuple, **kwargs):
    # noinspection PyProtectedMember
    return named_tuple._replace(**kwargs)


class EzArguments:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


@functools.lru_cache()
def ez_snake_case_to_camel_case(s: str):
    first, *others = s.split('_')
    return ''.join([first.lower(), *map(str.title, others)])


class EzAttrData:
    def __init__(self, **kwargs):
        self.set(**kwargs)

    def set(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def get(self, **kwargs):
        r = {}
        for k, v in kwargs.items():
            if hasattr(self, k):
                r[k] = getattr(self, k)
            else:
                r[k] = v
        return r
