#!/usr/bin/env python3
# encoding=utf8
import codecs
import fnmatch
import getpass
import html
import json
import locale
import os
import platform
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import urllib.parse
from collections import defaultdict
from contextlib import contextmanager
from glob import glob
from io import FileIO
from queue import Queue
from time import time
from typing import Iterable, Callable, Generator, Iterator, Tuple, Dict, List

import psutil
from filetype import filetype

from .tricks import make_kwargs_dict, NonBlockingCaller, meta_new_thread

if os.name == 'nt':
    from .nt_util import *
elif os.name == 'posix':
    from .posix_util import *

TEMPDIR = tempfile.gettempdir()


def fs_inplace_rename(src: str, pattern: str, replace: str, only_basename: bool = True, dry_run: bool = False):
    if only_basename:
        parent, basename = os.path.split(src)
        dst = os.path.join(parent, basename.replace(pattern, replace))
    else:
        dst = src.replace(pattern, replace)
    if src != dst:
        print('* {} ->\n  {}'.format(src, dst))
    if not dry_run:
        shutil.move(src, dst)


def fs_inplace_rename_regex(src: str, pattern: str, replace: str, only_basename: bool = True, dry_run: bool = False):
    if only_basename:
        parent, basename = os.path.split(src)
        dst = os.path.join(parent, re.sub(pattern, replace, basename))
    else:
        dst = re.sub(pattern, replace, src)
    if src != dst:
        print('* {} ->\n  {}'.format(src, dst))
    if not dry_run:
        shutil.move(src, dst)


def fs_legal_name(x: str, repl: str or dict = None, unescape_html=True, decode_url=True) -> str:
    if unescape_html:
        x = html.unescape(x)
    if decode_url:
        x = urllib.parse.unquote(x)
    if repl:
        if isinstance(repl, str):
            r = ILLEGAL_FS_CHARS_REGEX_PATTERN.sub(repl, x)
            # rl = len(repl)
            # if rl > 1:
            #     r = ILLEGAL_FS_CHARS_REGEX_PATTERN.sub(repl, x)
            # elif rl == 1:
            #     r = x.translate(str.maketrans(ILLEGAL_FS_CHARS, repl * ILLEGAL_FS_CHARS_LEN))
            # else:
            #     r = x.translate(str.maketrans('', '', ILLEGAL_FS_CHARS))
        elif isinstance(repl, dict):
            r = x.translate(repl)
        else:
            raise ValueError("Invalid repl '{}'".format(repl))
    else:
        r = x.translate(ILLEGAL_FS_CHARS_UNICODE_REPLACE_TABLE)
    return r


def fs_rename(src_path: str, dst_name_or_path: str = None, dst_ext: str = None, *,
              move_to_dir: str = None, stay_in_src_dir: bool = True, append_src_ext: bool = True) -> str:
    src_root, src_basename = os.path.split(src_path)
    src_before_ext, src_ext = os.path.splitext(src_basename)
    if dst_ext is not None:
        if dst_name_or_path is None:
            dst_name_or_path = src_before_ext + dst_ext
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


def fs_touch(filepath):
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
                 recursive: bool = True, strip_root: bool = True,
                 progress_queue: Queue = None) -> Generator:
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

    def put_progress(path):
        progress_queue.put(path)

    def no_progress(path):
        pass

    if progress_queue:
        update_progress = put_progress
    else:
        update_progress = no_progress

    if recursive:
        for t3e in os.walk(root):
            par, fn_list = pick_os_walk_tuple(*t3e)
            for fn in fn_list:
                if match(fn):
                    output_path = join_path(par, fn)
                    update_progress(output_path)
                    yield output_path
    else:
        for basename in os.listdir(root):
            real_path = os.path.join(root, basename)
            output_path = join_path(root, basename)
            if check(real_path) and match(basename):
                update_progress(output_path)
                yield output_path


class SubscriptableFileIO(FileIO):
    """slice data in FileIO object"""

    def __init__(self, file, mode='r+b', *args, **kwargs):
        """refer to doc string of io.FileIO"""
        super(SubscriptableFileIO, self).__init__(file, mode=mode, *args, **kwargs)
        try:
            self._size = os.path.getsize(file)
        except TypeError:
            self._size = os.path.getsize(self.name)

    def __len__(self):
        return self._size

    @property
    def size(self):
        return self._size

    def __getitem__(self, key: int or slice):
        orig_pos = self.tell()
        if isinstance(key, int):
            if key < 0:
                key = self.size + key
            self.seek(key)
            r = self.read(1)
        elif isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            if not start:
                start = 0
            elif start < 0:
                start = self.size + start
            if not stop:
                stop = self.size
            elif stop < 0:
                stop = self.size + stop
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
                key = self.size + key
            self.seek(key)
            r = self.write(value)
        elif isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            if not start:
                start = 0
            elif start < 0:
                start = self.size + start
            if not stop:
                stop = self.size
            elif stop < 0:
                stop = self.size + stop
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


def list_files(src, recursive=False, progress_queue: Queue = None) -> list:
    recur_kwargs = make_kwargs_dict(recursive=recursive, progress_queue=progress_queue)
    # if src is None:
    #     return list_files(clipboard.list_paths(exist_only=True), recursive=recursive)
    # elif isinstance(src, str):
    if isinstance(src, str):
        if os.path.isfile(src):
            return [src]
        elif os.path.isdir(src):
            return list(fs_find_iter(root=src, strip_root=False, **recur_kwargs))
        else:
            return [fp for fp in glob(src, recursive=recursive) if os.path.isfile(fp)]
    elif isinstance(src, (Iterable, Iterator)):
        r = []
        for s in src:
            r.extend(list_files(s, **recur_kwargs))
        return r
    elif isinstance(src, Clipboard):
        return list_files(src.list_paths(exist_only=True), **recur_kwargs)
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


def shrink_name(s: str, max_bytes=250, encoding='utf8', add_dots=True):
    shrunk = False
    limit = max_bytes - 3 if add_dots else max_bytes
    while len(s.encode(encoding=encoding)) > limit:
        s = s[:-1]
        shrunk = True
    return s + '...' if shrunk and add_dots else s


def get_names():
    class Names:
        hostname: str
        osname: str
        username: str

    r = Names()
    r.hostname = platform.node()
    r.osname = platform.system()
    r.username = getpass.getuser()
    return r


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
    monitoring = []
    monitor_stdout = bool(p.stdout)
    monitor_stderr = bool(p.stderr)
    if monitor_stdout:
        monitoring.append((NonBlockingCaller(p.stdout.read, 1), codecs.getincrementaldecoder(encoding)(), sys.stdout))
    if monitor_stderr:
        monitoring.append((NonBlockingCaller(p.stderr.read, 1), codecs.getincrementaldecoder(encoding)(), sys.stderr))
    t0 = time()
    while 1:
        if time() - t0 > timeout:
            for cp in psutil.Process(p.pid).children(recursive=True):
                cp.kill()
            p.kill()
            raise TimeoutError(p.args)
        for reader, decoder, output in monitoring:
            decoder: codecs.IncrementalDecoder
            try:
                b = reader.peek()
                if b:
                    t0 = time()
                    reader.call()
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
                        return r
                    sleep(wait)
            except reader.StillRunning:
                pass
            except Exception as e:
                raise e
