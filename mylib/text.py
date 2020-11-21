#!/usr/bin/env python3
# encoding=utf8
import locale
import re
from typing import Iterable, Iterator

from .tricks import dedup_list, deco_factory_args_choices
from .text_base import *


def regex_find(pattern, source, dedup: bool = False):
    findall = re.findall(pattern, source)
    r = []
    for e in findall:
        if dedup and e in r:
            continue
        else:
            r.append(e)
    return r


@deco_factory_args_choices({'logic': ('and', '&', 'AND', 'or', '|', 'OR')})
def simple_partial_query(pattern_list: Iterable[str], source_pool: Iterator[str],
                         logic: str = 'and',
                         ignore_case: bool = True, enable_regex: bool = False):
    if not enable_regex:
        pattern_list = [re.escape(p) for p in pattern_list]
    if ignore_case:
        flag_val = re.IGNORECASE
    else:
        flag_val = 0
    pl = [re.compile(p, flags=flag_val) for p in pattern_list]
    if logic in ('and', '&', 'AND'):
        r = [s for s in source_pool if not [p for p in pl if not p.search(s)]]
    elif logic in ('or', '|', 'OR'):
        r = [s for s in source_pool if [p for p in pl if p.search(s)]]
    else:
        raise ValueError('logic', logic)
    return dedup_list(r)


def dedup_periodical_str(s):
    # https://stackoverflow.com/a/29489919/7966259
    i = (s + s)[1:-1].find(s)
    if i == -1:
        return s
    else:
        return s[:i + 1]


def decode(b: bytes, encoding='u8'):
    try:
        return b.decode(encoding=encoding)
    except UnicodeDecodeError:
        return b.decode(encoding=locale.getdefaultlocale()[1])


def split_by_length_or_lf(x: str, length: int):
    parts = []
    while x:
        if len(x) > length:
            part = x[:length]
            stop = part.rfind('\n') + 1
            if stop:
                parts.append(x[:stop])
                x = x[stop:]
            else:
                parts.append(part)
                x = x[length:]
        else:
            parts.append(x)
            break
    return parts


def pattern_replace(s: str, pattern: str, replace: str, *, regex=False, ignore_case=False):
    if regex:
        if ignore_case:
            return re.sub(pattern, replace, s, flags=re.IGNORECASE)
        else:
            return re.sub(pattern, replace, s)
    else:
        if ignore_case:
            return re.sub(re.escape(pattern), re.escape(replace), s, flags=re.IGNORECASE)
        else:
            return s.replace(pattern, replace)


def find_words(s: str, allow_mix_non_word_chars='\''):
    if allow_mix_non_word_chars is True:
        return [p for p in s.split() if re.search(r'\w', p)]
    elif allow_mix_non_word_chars:
        pattern = fr'[\w{allow_mix_non_word_chars}]+'
        return [p.strip() for p in re.findall(pattern, s)]
    else:
        return re.findall(r'\w+', s)


