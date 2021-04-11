#!/usr/bin/env python3
# encoding=utf8
import codecs
import getpass
import platform
import shlex
import tempfile
from collections import defaultdict

import psutil
from filetype import filetype

from mylib.ez import *

if os.name == 'nt':
    from .ostk_nt import *
elif os.name == 'posix':
    from .ostk_posix import *
else:
    from .ostk_lite import *

TEMPDIR = tempfile.gettempdir()
HOSTNAME = platform.node()
OSNAME = platform.system()
USERNAME = getpass.getuser()


def check_file_ext(fp: str, ext_list: T.Iterable):
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
    with SubscriptableFileIO(filepath, 'rb+') as f:
        if total and f.size != total:
            f.truncate(total)
        elif f.size < stop:
            f.truncate(stop)
        f[start:stop] = data


def split_filename_tail(filepath, valid_tails) -> T.Tuple[str, str, str, str]:
    dirname, basename = os.path.split(filepath)
    file_non_ext, file_ext = os.path.splitext(basename)
    file_name, file_tail = os.path.splitext(file_non_ext)
    if file_tail in valid_tails:
        return dirname, file_name, file_tail, file_ext
    else:
        return dirname, file_non_ext, '', file_ext


def join_filename_tail(dirname, name_without_tail, tail, ext):
    return os.path.join(dirname, f'{name_without_tail}{tail}{ext}')


def group_filename_tail(filepath_list, valid_tails) -> T.Dict[T.Tuple[str, str], T.List[T.Tuple[str, str]]]:
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
    _out = io.BytesIO()
    _err = io.BytesIO()
    monitoring = []
    monitor_stdout = bool(p.stdout)
    monitor_stderr = bool(p.stderr)
    nb_caller = tricks_lite.NonBlockingCaller
    if monitor_stdout:
        monitoring.append(
            (nb_caller(p.stdout.read, 1), codecs.getincrementaldecoder(encoding)(), sys.stdout, _out))
    if monitor_stderr:
        monitoring.append(
            (nb_caller(p.stderr.read, 1), codecs.getincrementaldecoder(encoding)(), sys.stderr, _err))
    t0 = time.perf_counter()
    while 1:
        if time.perf_counter() - t0 > timeout:
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
                    t0 = time.perf_counter()
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


def set_console_title___try(title: str):
    try:
        set_console_title(title)
    except NameError:
        pass
