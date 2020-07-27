#!/usr/bin/env python3
# encoding=utf8
import fnmatch
import json
import os
import shutil
import signal
import sys
import tempfile
from contextlib import contextmanager
from io import FileIO
from typing import Iterable, Callable

if os.name == 'nt':
    from .nt_util import *
elif os.name == 'posix':
    from .posix_util import *
else:
    raise ImportError("Off-design OS: '{}'".format(os.name))


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


def fs_rename(src_path: str, dst_name: str, move_to: str = None, keep_ext: bool = True):
    old_root, old_basename = os.path.split(src_path)
    _, old_ext = os.path.splitext(old_basename)
    if move_to:
        new_path = os.path.join(move_to, dst_name)
    else:
        new_path = os.path.join(old_root, dst_name)
    if keep_ext:
        new_path = new_path + old_ext
    shutil.move(src_path, new_path)


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


def ensure_chdir(dest: str):
    if not os.path.isdir(dest):
        os.makedirs(dest, exist_ok=True)
    os.chdir(dest)


@contextmanager
def pushd_context(dest: str, ensure_dest: bool = False):
    if ensure_dest:
        cd = ensure_chdir
    else:
        cd = os.chdir
    prev = os.getcwd()
    cd(dest)
    to_raise = None
    try:
        yield
    except Exception as e:
        to_raise = e
    finally:
        cd(prev)
        if to_raise:
            raise to_raise


def ensure_open_file(file, mode='r', **kwargs):
    parent, basename = os.path.split(file)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    if not os.path.isfile(file):
        if os.path.exists(file):
            raise ValueError("non-file already exists: {}".format(file))
        else:
            open(file, 'w').close()
    return open(file, mode, **kwargs)


def read_json_file(file, default=None, **kwargs) -> dict:
    with ensure_open_file(file, 'r') as jf:
        try:
            d = json.load(jf, **kwargs)
        except json.decoder.JSONDecodeError:
            d = default or {}
    return d


def write_json_file(file, data, **kwargs):
    with ensure_open_file(file, 'w') as jf:
        json.dump(data, jf, **kwargs)


def check_file_ext(fp: str, ext_list: Iterable):
    return os.path.isfile(fp) and os.path.splitext(fp)[-1].lower() in ext_list


def fs_find_gen(root: str = None, pattern: str or Callable = None, regex: bool = False, folder: bool = False):
    root = root or '.'

    if folder:
        def pick(parent, folder_list, file_list):
            return parent, folder_list
    else:
        def pick(parent, folder_list, file_list):
            return parent, file_list

    if pattern is None:
        def match(fname):
            return True
    elif isinstance(pattern, str):
        if regex:
            def match(fname):
                if re.search(pattern, fn):
                    return True
                else:
                    return False
        else:
            def match(fname):
                return fnmatch.fnmatch(fn, pattern)
    elif isinstance(pattern, Callable):
        match = pattern
    else:
        raise ValueError("invalid pattern: '{}', should be `str` or `function(fname)`")

    for t3e in os.walk(root):
        par, fn_list = pick(*t3e)
        for fn in fn_list:
            if match(fn):
                yield os.path.join(par, fn)


class FileSlice:
    io = None
    file_size = None

    def __init__(self, name, *args, **kwargs):
        """refer to doc string of io.FileIO"""
        self.io = FileIO(name, *args, **kwargs)
        self.file_size = os.path.getsize(name)

    def __len__(self):
        return self.file_size

    def __getitem__(self, item: int or slice):
        if isinstance(item, int):
            if item < 0:
                item = len(self) + item
            self.io.seek(item)
            return self.io.read(1)
        elif isinstance(item, slice):
            start, stop, step = item.start, item.stop, item.step
            if not start:
                start = 0
            if not stop:
                stop = len(self)
            if not step or step == 1:
                self.io.seek(start)
                return self.io.read(stop - start)
            else:
                return [self[i] for i in range(*item.indices(len(self)))]
        else:
            raise TypeError("'{}' is not int or slice".format(item))
