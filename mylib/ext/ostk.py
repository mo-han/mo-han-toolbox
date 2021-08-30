#!/usr/bin/env python3
import shlex
from collections import defaultdict

from mylib.easy import *

if os.name == 'nt':
    from .ostk_nt import *
elif os.name == 'posix':
    from .ostk_posix import *
else:
    from mylib.easy.ostk import *


def get_screen_size_via_tkinter():
    import tkinter
    tk = tkinter.Tk()
    w = tk.winfo_screenwidth()
    h = tk.winfo_screenheight()
    tk.destroy()
    return w, h


def check_file_ext(fp: str, ext_list: T.Iterable):
    return os.path.isfile(fp) and os.path.splitext(fp)[-1].lower() in ext_list


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
    with io.SubscriptableFileIO(filepath, 'rb+') as f:
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
