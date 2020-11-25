#!/usr/bin/env python3
# encoding=utf8
import locale
import unicodedata

from .ez import *
from .tricks_ez import deco_factory_args_choices, dedup_list

ATTENTION_DO_NO_USE_THIS = __name__

CR = '\r'
LF = '\n'
CRLF = '\r\n'


def visual_len(s: str):
    eaw = unicodedata.east_asian_width
    n = len(s)
    n += sum([1 for c in s if eaw(c) == 'W'])
    return n


def list2col_str(x: Iterable or Iterator, width, *, horizontal=False, sep=2):
    """transfer list items into a single `str` in format of columns"""
    sep_s = ' ' * sep
    text_l = [s for s in x]
    max_len = max([visual_len(s) for s in text_l])
    n = len(text_l)
    col_w = max_len + sep
    col_n = width // col_w or 1
    row_n = n // col_n + bool(n % col_n)
    if horizontal:
        rows_l = [text_l[i:i + col_n] for i in range(0, n, col_n)]
    else:
        rows_l = [text_l[i::row_n] for i in range(0, row_n)]
    lines_l = [sep_s.join([f'{s}{" " * (max_len - visual_len(s))}' for s in row]) for row in rows_l]
    return '\n'.join(lines_l)


def decode_locale(b: bytes, encoding='u8'):
    try:
        return b.decode(encoding=encoding)
    except UnicodeDecodeError:
        return b.decode(encoding=locale.getdefaultlocale()[1])


def find_words(s: str, allow_mix_non_word_chars='\''):
    if allow_mix_non_word_chars is True:
        return [p for p in s.split() if re.search(r'\w', p)]
    elif allow_mix_non_word_chars:
        pattern = fr'[\w{allow_mix_non_word_chars}]+'
        return [p.strip() for p in re.findall(pattern, s)]
    else:
        return re.findall(r'\w+', s)


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


def split_by_length_or_newline(x: str, length: int):
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


def dedup_periodical_str(s):
    # https://stackoverflow.com/a/29489919/7966259
    i = (s + s)[1:-1].find(s)
    if i == -1:
        return s
    else:
        return s[:i + 1]


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


def regex_find(pattern, source, dedup: bool = False):
    findall = re.findall(pattern, source)
    r = []
    for e in findall:
        if dedup and e in r:
            continue
        else:
            r.append(e)
    return r


def ellipt_middle(s: str, limit=250, *, the_ellipsis: str = '...', encoding: str = None):
    half_limit = (limit - len(the_ellipsis.encode(encoding=encoding) if encoding else the_ellipsis)) // 2
    common_params = dict(encoding=encoding, the_ellipsis='', limit=half_limit)
    half_s_len = len(s) // 2 + 1
    left = ellipt_end(s[:half_s_len], left_side=True, **common_params)
    right = ellipt_end(s[half_s_len:], left_side=False, **common_params)
    lr = f'{left}{right}'
    if the_ellipsis:
        if len(lr) == len(s):
            return s
        else:
            return f'{left}{the_ellipsis}{right}'
    else:
        return f'{left}{right}'


def ellipt_end(s: str, limit=250, *, the_ellipsis: str = '...', encoding: str = None, left_side=False):
    if encoding:
        def length(x: str):
            return len(x.encode(encoding=encoding))
    else:
        def length(x: str):
            return len(x)
    ellipsis_len = length(the_ellipsis)
    if left_side:
        def strip(x: str):
            return x[1:]
    else:
        def strip(x: str):
            return x[:-1]
    shrunk = False
    limit = limit - ellipsis_len
    if limit <= 0:
        raise ValueError('limit too small', limit)
    while length(s) > limit:
        s = strip(s)
        shrunk = True
    if shrunk:
        if left_side:
            return f'{the_ellipsis}{s}'
        else:
            return f'{s}{the_ellipsis}'
    else:
        return s
