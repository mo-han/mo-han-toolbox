#!/usr/bin/env python3
# encoding=utf8

import re
from typing import Iterable, Iterator
from .tricks import dedup_list, decorator_factory_args_choices


def regex_find(pattern, source, dedup: bool = False):
    findall = re.findall(pattern, source)
    r = []
    for e in findall:
        if dedup and e in r:
            continue
        else:
            r.append(e)
    return r


@decorator_factory_args_choices({'logic': ('and', '&', 'AND', 'or', '|', 'OR')})
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
