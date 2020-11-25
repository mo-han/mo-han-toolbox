#!/usr/bin/env python3
# encoding=utf8
import contextlib
import fnmatch
import glob
import html
import itertools
import json
import urllib.parse

import mylib.text_ez
from . import os_xp
from .ez import *


def inplace_pattern_rename(src_path: str, pattern: str, repl: str, *,
                           only_basename=True, ignore_case=False, regex=False, dry_run=False
                           ) -> str or None:
    if only_basename:
        parent, basename = os.path.split(src_path)
        dst_path = os.path.join(parent,
                                mylib.text_ez.pattern_replace(src_path, pattern, repl, regex=regex, ignore_case=ignore_case))
    else:
        dst_path = mylib.text_ez.pattern_replace(src_path, pattern, repl, regex=regex, ignore_case=ignore_case)
    if not dry_run:
        shutil.move(src_path, dst_path)
    if src_path != dst_path:
        return dst_path


def match_ignore_case(name: str, pattern: str):
    return bool(fnmatch.fnmatch(name, pattern))


def match(name: str, pattern: str):
    return bool(fnmatch.fnmatchcase(name, pattern))


def regex_match_ignore_case(name: str, pattern: str):
    return bool(re.search(pattern, name, flags=re.IGNORECASE))


def regex_match(name: str, pattern: str):
    return bool(re.search(pattern, name))


def func_factory_match_pattern(regex: bool, ignore_case: bool):
    return {
        (False, False): match, (False, True): match_ignore_case,
        (True, False): regex_match, (True, True): regex_match_ignore_case
    }[(bool(regex), bool(ignore_case))]


def find_iter(start_path: str, find_type: str, pattern: str = None, *,
              abspath=False, recursive=True, regex=False, ignore_case=False):
    find_files = 'f' in find_type
    find_dirs = 'd' in find_type
    pattern = pattern or ('.*' if regex else '*')
    start_path = os.path.abspath(start_path) if abspath else start_path
    match_func = func_factory_match_pattern(regex=regex, ignore_case=ignore_case)
    basename = os.path.basename
    if os.path.isfile(start_path):
        if find_files and match_func(basename(start_path), pattern):
            yield start_path
        return
    if os.path.isdir(start_path):
        if find_dirs and match_func(basename(start_path), pattern):
            yield start_path
        if not recursive:
            return
    # p,d,f = dirpath, dirnames, filenames
    # n = name = dirname/filename from dirnames/filenames
    walk_pdf = ((p, d, f) for p, d, f in (os.walk(start_path)))
    if find_files and find_dirs:
        chain_iter = itertools.chain
        yield from (os.path.join(p, n) for p, d, f in walk_pdf for n in chain_iter(d, f) if match_func(n, pattern))
    elif find_files:
        yield from (os.path.join(p, n) for p, d, f in walk_pdf for n in f if match_func(n, pattern))
    elif find_dirs:
        yield from (os.path.join(p, n) for p, d, f in walk_pdf for n in d if match_func(n, pattern))
    else:
        return


def make_path(*paths, absolute=False, follow_link=False, relative=False, user_home=True, env_var=True):
    if absolute and relative:
        raise ValueError('both `absolute` and `relative` are enabled')
    path = os.path.join(*paths)
    if follow_link:
        path = os.path.realpath(path)
    if absolute:
        path = os.path.abspath(path)
    elif relative is True:
        path = os.path.relpath(path)
    elif relative:
        path = os.path.relpath(path, relative)
    if user_home:
        path = os.path.expanduser(path)
    if env_var:
        path = os.path.expandvars(path)
    return path


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


def write_json_file(file, data, *, indent=None, utf8: bool = True, **kwargs):
    file_kwargs = {}
    if utf8:
        file_kwargs['encoding'] = 'utf8'
    with ensure_open_file(file, 'w', **file_kwargs) as jf:
        json.dump(data, jf, indent=indent, ensure_ascii=not utf8, **kwargs)


def touch(filepath):
    try:
        os.utime(filepath)
    except OSError:
        open(filepath, 'a').close()


def x_rename(src_path: str, dst_name_or_path: str = None, dst_ext: str = None, *,
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


def safe_name(name: str, repl: str or dict = None, unescape_html=True, decode_url=True) -> str:
    if unescape_html:
        name = html.unescape(name)
    if decode_url:
        name = urllib.parse.unquote(name)
    if repl:
        if isinstance(repl, str):
            r = os_xp.ILLEGAL_FS_CHARS_REGEX_PATTERN.sub(repl, name)
            # rl = len(repl)
            # if rl > 1:
            #     r = ILLEGAL_FS_CHARS_REGEX_PATTERN.sub(repl, x)
            # elif rl == 1:
            #     r = x.translate(str.maketrans(ILLEGAL_FS_CHARS, repl * ILLEGAL_FS_CHARS_LEN))
            # else:
            #     r = x.translate(str.maketrans('', '', ILLEGAL_FS_CHARS))
        elif isinstance(repl, dict):
            r = name.translate(repl)
        else:
            raise TypeError("Invalid repl '{}'".format(repl))
    else:
        r = name.translate(os_xp.ILLEGAL_FS_CHARS_UNICODE_REPLACE_TABLE)
    return r


def read_sqlite_dict_file(filepath, *, with_dill=False, **kwargs):
    if with_dill:
        from .tricks import module_sqlitedict_with_dill
        sqlitedict = module_sqlitedict_with_dill(dill_detect_trace=True)
    else:
        import sqlitedict
    with sqlitedict.SqliteDict(filepath, **kwargs) as sd:
        return dict(sd)


def write_sqlite_dict_file(filepath, data, *, with_dill=False, dill_detect_trace=False, update_only=False, **kwargs):
    if with_dill:
        from .tricks import module_sqlitedict_with_dill
        sqlitedict = module_sqlitedict_with_dill(dill_detect_trace=dill_detect_trace)
    else:
        import sqlitedict
    with sqlitedict.SqliteDict(filepath, **kwargs) as sd:
        if not update_only:
            sd.clear()
        sd.update(data)
        sd.commit()


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


@contextlib.contextmanager
def ctx_pushd(dst: str, ensure_dst: bool = False):
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


def ensure_chdir(dest: str):
    if not os.path.isdir(dest):
        os.makedirs(dest, exist_ok=True)
    os.chdir(dest)


def path_or_glob(pathname, *, recursive=False):
    if os.path.exists(pathname):
        return [pathname]
    else:
        return glob.glob(pathname, recursive=recursive)
