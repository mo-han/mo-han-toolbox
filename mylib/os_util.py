#!/usr/bin/env python3
# encoding=utf8
import fnmatch
import json
import os
import shlex
import shutil
import signal
import sys
import tempfile
from contextlib import contextmanager
from io import FileIO
from typing import Iterable, Callable, Generator

if os.name == 'nt':
    from .nt_util import *
elif os.name == 'posix':
    from .posix_util import *


def regex_move_path(source: str, pattern: str, replace: str, only_basename: bool = True, dry_run: bool = False):
    if only_basename:
        parent, basename = os.path.split(source)
        dst = os.path.join(parent, re.sub(pattern, replace, basename))
    else:
        dst = re.sub(pattern, replace, source)
    print('{}\n-> {}'.format(source, dst))
    if not dry_run:
        shutil.move(source, dst)


def legal_fs_name(x: str, repl: str or dict = None) -> str:
    if repl:
        if isinstance(repl, str):
            rl = len(repl)
            if rl > 1:
                legal = ILLEGAL_FS_CHARS_REGEX_PATTERN.sub(repl, x)
            elif rl == 1:
                legal = x.translate(str.maketrans(ILLEGAL_FS_CHARS, repl * ILLEGAL_FS_CHARS_LEN))
            else:
                legal = x.translate(str.maketrans('', '', ILLEGAL_FS_CHARS))
        elif isinstance(repl, dict):
            legal = x.translate(repl)
        else:
            raise ValueError("Invalid repl '{}'".format(repl))
    else:
        legal = x.translate(ILLEGAL_FS_CHARS_UNICODE_REPLACE_TABLE)
    return legal


def fs_rename(src_path: str, dst_name_or_path: str = None, dst_ext: str = None, *,
              move_to_dir: str = None, stay_in_src_dir: bool = True, append_src_ext: bool = True) -> str:
    src_root, src_basename = os.path.split(src_path)
    src_non_ext, src_ext = os.path.splitext(src_basename)
    if dst_ext is not None:
        if dst_name_or_path is None:
            dst_name_or_path = src_non_ext + dst_ext
        else:
            dst_name_or_path += dst_ext
    if move_to_dir:
        dst_path = os.path.join(move_to_dir, dst_name_or_path)
    elif stay_in_src_dir:
        dst_path = os.path.join(src_root, dst_name_or_path)
    else:
        dst_path = dst_name_or_path
    if append_src_ext:
        dst_path = dst_path + src_ext
    return shutil.move(src_path, dst_path)


def ensure_sigint_signal():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'


TEMPDIR = tempfile.gettempdir()


def real_join_path(path, *paths, expanduser: bool = True, expandvars: bool = True):
    """realpath(join(...))"""
    if expanduser:
        path = os.path.expanduser(path)
        paths = [os.path.expanduser(p) for p in paths]
    if expandvars:
        path = os.path.expandvars(path)
        paths = [os.path.expandvars(p) for p in paths]
    return os.path.realpath(os.path.join(path, *paths))


def relative_join_path(path, *paths, start_path: str = None, expanduser: bool = True, expandvars: bool = True):
    """relpath(join(...))"""
    if expanduser:
        path = os.path.expanduser(path)
        paths = [os.path.expanduser(p) for p in paths]
    if expandvars:
        path = os.path.expandvars(path)
        paths = [os.path.expandvars(p) for p in paths]
    return os.path.relpath(os.path.join(path, *paths), start=start_path)


def ensure_chdir(dest: str):
    if not os.path.isdir(dest):
        os.makedirs(dest, exist_ok=True)
    os.chdir(dest)


@contextmanager
def pushd_context(dst: str, ensure_dst: bool = False):
    if ensure_dst:
        cd = ensure_chdir
    else:
        cd = os.chdir
    prev = os.getcwd()
    cd(dst)
    saved_error = None
    try:
        yield
    except Exception as e:
        saved_error = e
    finally:
        cd(prev)
        if saved_error:
            raise saved_error


def ensure_open_file(filepath, mode='r', **kwargs):
    parent, basename = os.path.split(filepath)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    if not os.path.isfile(filepath):
        try:
            open(filepath, 'a').close()
        except PermissionError as e:
            if os.path.isdir(filepath):
                raise FileExistsError("path used by directory '{}'".format(filepath))
            else:
                raise e
    return open(filepath, mode, **kwargs)


def touch(filepath):
    try:
        os.utime(filepath)
    except OSError:
        open(filepath, 'a').close()


def read_json_file(file, default=None, utf8: bool = True, **kwargs) -> dict:
    file_kwargs = {}
    if utf8:
        file_kwargs['encoding'] = 'utf8'
    with ensure_open_file(file, 'r', **file_kwargs) as jf:
        try:
            d = json.load(jf, **kwargs)
        except json.decoder.JSONDecodeError:
            d = default or {}
    return d


def write_json_file(file, data, utf8: bool = True, **kwargs):
    file_kwargs = {}
    if utf8:
        file_kwargs['encoding'] = 'utf8'
    with ensure_open_file(file, 'w', **file_kwargs) as jf:
        json.dump(data, jf, ensure_ascii=not utf8, **kwargs)


def check_file_ext(fp: str, ext_list: Iterable):
    return os.path.isfile(fp) and os.path.splitext(fp)[-1].lower() in ext_list


def fs_find_iter(pattern: str or Callable = None, root: str = '.',
                 regex: bool = False, find_dir_instead_of_file: bool = False,
                 recursive: bool = True, strip_root: bool = True) -> Generator:
    if find_dir_instead_of_file:
        def pick_os_walk_tuple(parent, folder_list, file_list):
            return parent, folder_list

        def check(x):
            return os.path.isdir(x)
    else:
        def pick_os_walk_tuple(parent, folder_list, file_list):
            return parent, file_list

        def check(x):
            return os.path.isfile(x)

    if strip_root:
        def join_path(path, *paths):
            return relative_join_path(path, *paths, start_path=root)
    else:
        join_path = os.path.join

    if pattern is None:
        def match(fname):
            return True
    elif isinstance(pattern, str):
        if regex:
            def match(fname):
                if re.search(pattern, fname):
                    return True
                else:
                    return False
        else:
            def match(fname):
                return fnmatch.fnmatch(fname, pattern)
    elif isinstance(pattern, Callable):
        match = pattern
    else:
        raise ValueError("invalid pattern: '{}', should be `str` or `function(fname)`")

    if recursive:
        for t3e in os.walk(root):
            par, fn_list = pick_os_walk_tuple(*t3e)
            for fn in fn_list:
                if match(fn):
                    yield join_path(par, fn)
    else:
        for basename in os.listdir(root):
            path = join_path(root, basename)
            if check(path) and match(basename):
                yield path


class SubscriptableFileIO(FileIO):
    def __init__(self, file, mode='r', *args, **kwargs):
        """refer to doc string of io.FileIO"""
        super(SubscriptableFileIO, self).__init__(file, mode=mode, *args, **kwargs)
        try:
            self.file_size = os.path.getsize(file)
        except TypeError:
            self.file_size = os.path.getsize(self.name)

    def __len__(self):
        return self.file_size

    def __getitem__(self, key: int or slice):
        orig_pos = self.tell()
        if isinstance(key, int):
            if key < 0:
                key = len(self) + key
            self.seek(key)
            r = self.read(1)
        elif isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            if not start:
                start = 0
            elif start < 0:
                start = len(self) + start
            if not stop:
                stop = len(self)
            elif stop < 0:
                stop = len(self) + stop
            size = stop - start
            if size <= 0:
                r = b''
            elif not step or step == 1:
                self.seek(start)
                r = self.read(size)
            else:
                r = self.read(size)[::step]
        else:
            raise TypeError("'{}' is not int or slice".format(key))
        self.seek(orig_pos)
        return r

    def __setitem__(self, key: int or slice, value: bytes):
        orig_pos = self.tell()
        if isinstance(key, int):
            if len(value) != 1:
                raise ValueError("overflow write", value)
            if key < 0:
                key = len(self) + key
            self.seek(key)
            r = self.write(value)
        elif isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            if not start:
                start = 0
            elif start < 0:
                start = len(self) + start
            if not stop:
                stop = len(self)
            elif stop < 0:
                stop = len(self) + stop
            size = stop - start
            if size <= 0:
                r = 0
            elif not step or step == 1:
                if len(value) <= size:
                    self.seek(start)
                    r = self.write(value)
                else:
                    raise NotImplementedError('overflow write')
            else:
                raise NotImplementedError('non-sequential write')
        else:
            raise TypeError("'{}' is not int or slice".format(key))
        self.seek(orig_pos)
        return r


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
