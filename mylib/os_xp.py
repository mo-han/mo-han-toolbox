#!/usr/bin/env python3
# encoding=utf8
import codecs
import getpass
import locale
import platform
import shlex
import tempfile
from collections import defaultdict
from glob import glob
from io import BytesIO
from queue import Queue

import psutil
from filetype import filetype

from . import tricks_ez
from ._deprecated import fs_find_iter
from .os_ez import *

assert (tricks_ez,)

if os.name == 'nt':
    from .os_nt import *
elif os.name == 'posix':
    from .os_posix import *
else:
    raise NotImplementedError(os.name)

TEMPDIR = tempfile.gettempdir()
HOSTNAME = platform.node()
OSNAME = platform.system()
USERNAME = getpass.getuser()


def check_file_ext(fp: str, ext_list: Iterable):
    return os.path.isfile(fp) and os.path.splitext(fp)[-1].lower() in ext_list


def shlex_join(split):
    try:
        return shlex.join(split)
    except AttributeError:
        return ' '.join([shlex.quote(s) for s in split])


def shlex_double_quotes_join(split):
    def quote_one(s):
        t = shlex.quote(s)
        if t.startswith("'") and t.endswith("'"):
            return '"{}"'.format(s)
        else:
            return s

    return ' '.join([quote_one(s) for s in split])


def file_offset_write(file, offset: int, data):
    with open(file, 'r+b') as f:
        f.seek(offset)
        f.write(data)


def file_offset_read(file, offset: int, length: int = None, end: int = None):
    if end:
        length = end - offset
    with open(file, 'r+b') as f:
        f.seek(offset)
        if length:
            return f.read(length)
        else:
            return f.read()


def write_file_chunk(filepath: str, start: int, stop: int, data: bytes, total: int = None):
    # if not 0 <= start <= stop:
    #     raise ValueError('violate 0 <= start({}) <= stop({})'.format(start, stop))
    # if len(data) >= stop - start:
    #     raise ValueError('data length > stop - start')
    with SubscriptableFileIO(filepath) as f:
        if total and f.size != total:
            f.truncate(total)
        elif f.size < stop:
            f.truncate(stop)
        f[start:stop] = data


def list_files(src: str or Iterable or Iterator or Clipboard, recursive=False, progress_queue: Queue = None) -> list:
    common_kwargs = dict(recursive=recursive, progress_queue=progress_queue)
    # if src is None:
    #     return list_files(clipboard.list_paths(exist_only=True), recursive=recursive)
    # elif isinstance(src, str):
    if isinstance(src, str):
        if os.path.isfile(src):
            return [src]
        elif os.path.isdir(src):
            return list(fs_find_iter(root=src, strip_root=False, **common_kwargs))
        else:
            return [fp for fp in glob(src, recursive=recursive) if os.path.isfile(fp)]
    elif isinstance(src, (Iterable, Iterator)):
        r = []
        for s in src:
            r.extend(list_files(s, **common_kwargs))
        return r
    elif isinstance(src, Clipboard):
        return list_files(src.list_paths(exist_only=True), **common_kwargs)
    else:
        raise TypeError('invalid source', src)


def list_dirs(src: str or Iterable or Iterator or Clipboard, recursive=False, progress_queue: Queue = None) -> list:
    common_kwargs = dict(recursive=recursive, progress_queue=progress_queue)
    if isinstance(src, str):
        if os.path.isdir(src):
            dirs = [src]
            if recursive:
                dirs.extend(
                    list(fs_find_iter(root=src, strip_root=False, find_dir_instead_of_file=True, **common_kwargs)))
            return dirs
        else:
            return [p for p in glob(src, recursive=recursive) if os.path.isdir(p)]
    elif isinstance(src, (Iterable, Iterator)):
        dirs = []
        for s in src:
            dirs.extend(list_dirs(s, **common_kwargs))
        return dirs
    elif isinstance(src, Clipboard):
        return list_dirs(src.list_paths(exist_only=True), **common_kwargs)
    else:
        raise TypeError('invalid source', src)


def split_filename_tail(filepath, valid_tails) -> Tuple[str, str, str, str]:
    dirname, basename = os.path.split(filepath)
    file_non_ext, file_ext = os.path.splitext(basename)
    file_name, file_tail = os.path.splitext(file_non_ext)
    if file_tail in valid_tails:
        return dirname, file_name, file_tail, file_ext
    else:
        return dirname, file_non_ext, '', file_ext


def join_filename_tail(dirname, name_without_tail, tail, ext):
    return os.path.join(dirname, f'{name_without_tail}{tail}{ext}')


def group_filename_tail(filepath_list, valid_tails) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    rv = defaultdict(list)
    for fp in filepath_list:
        dn, fn, tail, ext = split_filename_tail(fp, valid_tails)
        rv[(dn, fn)].append((tail, ext))
    return rv


def filter_filename_tail(filepath_list, valid_tails, filter_tails, filter_extensions):
    rv = []
    for (dn, fn), tail_ext in group_filename_tail(filepath_list, valid_tails).items():
        for tail, ext in tail_ext:
            if tail in filter_tails or ext in filter_extensions:
                rv.append((dn, fn, tail, ext))
    return rv


def filetype_is(filepath, keyword):
    guess = filetype.guess(filepath)
    return guess and keyword in guess.mime


class ProcessTTYFrozen(TimeoutError):
    pass


def monitor_sub_process_tty_frozen(p: subprocess.Popen, timeout=30, wait=1,
                                   encoding=None, ignore_decode_error=True,
                                   ):
    def decode(inc_decoder: codecs.IncrementalDecoder, new_bytes: bytes) -> str or None:
        chars = inc_decoder.decode(new_bytes)
        if chars:
            inc_decoder.reset()
            return chars

    if not encoding:
        encoding = locale.getdefaultlocale()[1]
    _out = BytesIO()
    _err = BytesIO()
    monitoring = []
    monitor_stdout = bool(p.stdout)
    monitor_stderr = bool(p.stderr)
    nb_caller = tricks_ez.NonBlockingCaller
    if monitor_stdout:
        monitoring.append(
            (nb_caller(p.stdout.read, 1), codecs.getincrementaldecoder(encoding)(), sys.stdout, _out))
    if monitor_stderr:
        monitoring.append(
            (nb_caller(p.stderr.read, 1), codecs.getincrementaldecoder(encoding)(), sys.stderr, _err))
    t0 = time()
    while 1:
        if time() - t0 > timeout:
            for p in psutil.Process(p.pid).children(recursive=True):
                p.kill()
            p.kill()
            _out.seek(0)
            _err.seek(0)
            raise ProcessTTYFrozen(p, _out, _err)
        for nb_reader, decoder, output, bytes_io in monitoring:
            decoder: codecs.IncrementalDecoder
            try:
                b = nb_reader.get(wait)
                if b:
                    t0 = time()
                    bytes_io.write(b)
                    nb_reader.run()
                    if output:
                        try:
                            s = decode(decoder, b)
                            if s:
                                decoder.reset()
                                output.write(s)
                        except UnicodeDecodeError:
                            if ignore_decode_error:
                                decoder.reset()
                                continue
                            else:
                                raise
                else:
                    r = p.poll()
                    if r is not None:
                        _out.seek(0)
                        _err.seek(0)
                        return p, _out, _err
                    sleep(wait)
            except nb_reader.StillRunning:
                pass
            except Exception as e:
                raise e


def split_filename(path):
    """path -> parent_dir, name, ext"""
    p, b = os.path.split(path)
    n, e = os.path.splitext(b)
    return p, n, e


def join_filename(parent_path, name_without_ext, extension):
    """parent_dir, name, ext -> path"""
    return os.path.join(parent_path, name_without_ext + extension)


def set_console_title___try(title: str):
    try:
        set_console_title(title)
    except NameError:
        pass
