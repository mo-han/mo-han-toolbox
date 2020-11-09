#!/usr/bin/env python3
# encoding=utf8
import itertools
import os
import re
import shutil
from typing import Iterable, Iterator

from .text import replace
from .tricks import meta_deco_args_choices
import fnmatch


def rename_inplace(src_path: str, pattern: str, replace: str, *,
                   only_basename=True, ignore_case=False, regex=False, dry_run=False
                   ) -> str or None:
    if only_basename:
        parent, basename = os.path.split(src_path)
        dst_path = os.path.join(parent, replace(src_path, pattern, replace, regex=regex, ignore_case=ignore_case))
    else:
        dst_path = replace(src_path, pattern, replace, regex=regex, ignore_case=ignore_case)
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


def meta_func_match_pattern(regex: bool, ignore_case: bool):
    return {
        (False, False): match, (False, True): match_ignore_case,
        (True, False): regex_match, (True, True): regex_match_ignore_case
    }[(bool(regex), bool(ignore_case))]


def find_iter(start_path: str, find_files: bool, find_dirs: bool, pattern: str = None, *,
              abspath=False, recursive=True, regex=False, ignore_case=False):
    pattern = pattern or ('.*' if regex else '*')
    start_path = os.path.abspath(start_path) if abspath else start_path
    match_func = meta_func_match_pattern(regex=regex, ignore_case=ignore_case)
    if os.path.isfile(start_path):
        if find_files and match_func(start_path, pattern):
            yield start_path
            return
        else:
            return
    if os.path.isdir(start_path) and not recursive and match_func(start_path, pattern):
        if find_dirs:
            yield start_path
            return
        else:
            return
    walk_pdf = ((p, d, f) for p, d, f in (os.walk(start_path)))
    # p,d,f = dirpath, dirnames, filenames
    # n = name = dirname/filename from dirnames/filenames
    if find_files and find_dirs:
        chain_iter = itertools.chain
        yield from (os.path.join(p, n) for p, d, f in walk_pdf for n in chain_iter(d, f) if match_func(n, pattern))
    elif find_files:
        yield from (os.path.join(p, n) for p, d, f in walk_pdf for n in f if match_func(n, pattern))
    elif find_dirs:
        yield from (os.path.join(p, n) for p, d, f in walk_pdf for n in d if match_func(n, pattern))
    else:
        return
