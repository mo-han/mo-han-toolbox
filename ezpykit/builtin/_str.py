#!/usr/bin/env python3
import unicodedata

from ezpykit.metautil import decofac_add_method_to_class
from ezpykit.stdlib import typing as T

CR = '\r'
LF = '\n'
CRLF = '\r\n'


class ezstr(str):
    def get_width(self: str):
        eaw = unicodedata.east_asian_width
        n = len(self)
        n += sum([1 for c in self if eaw(c) == 'W'])
        return n

    def ellipt_middle(self: str, max_len: int, *, the_ellipsis: str = '...', encoding: str = None):
        half_limit = (max_len - len(the_ellipsis.encode(encoding=encoding) if encoding else the_ellipsis)) // 2
        common_params = dict(encoding=encoding, the_ellipsis='', max_len=half_limit)
        half_s_len = len(self) // 2 + 1
        left = ezstr.ellipt_end(self[:half_s_len], left_side=False, **common_params)
        right = ezstr.ellipt_end(self[half_s_len:], left_side=True, **common_params)
        lr = f'{left}{right}'
        if the_ellipsis:
            if len(lr) == len(self):
                return self
            else:
                return f'{left}{the_ellipsis}{right}'
        else:
            return f'{left}{right}'

    def ellipt_end(self: str, max_len: int, *, the_ellipsis: str = '...', encoding: str = None, left_side=False):
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
        max_len = max_len - ellipsis_len
        if max_len <= 0:
            raise ValueError('limit too small', max_len)
        s = self
        while length(s) > max_len:
            s = strip(s)
            shrunk = True
        if shrunk:
            if left_side:
                return f'{the_ellipsis}{s}'
            else:
                return f'{s}{the_ellipsis}'
        else:
            return s

    def unicode_normalize(self: str, compose=False, compatibility=False):
        forms = {(False, False): 'D', (False, True): 'KD', (True, False): 'C', (True, True): 'KC'}
        form = f'NF{forms[(bool(compose), bool(compatibility))]}'
        return unicodedata.normalize(form, self)

    def remove_accent_chars(self: str) -> str:
        return u"".join([c for c in (unicodedata.normalize('NFKD', self)) if not unicodedata.combining(c)])

    def remove_accent_chars_join(self: str):
        # answer by MiniQuark
        # https://stackoverflow.com/a/517974/7966259
        return u"".join([c for c in unicodedata.normalize('NFKD', self) if not unicodedata.combining(c)])


if hasattr(ezstr, 'removeprefix'):
    str_remove_prefix = str.removeprefix
else:
    @decofac_add_method_to_class(ezstr, 'removeprefix')
    def str_remove_prefix(s: str, prefix: str):
        return s[len(prefix):] if s.startswith(prefix) else s

if hasattr(ezstr, 'removesuffix'):
    str_remove_suffix = str.removesuffix
else:
    @decofac_add_method_to_class(ezstr, 'removesuffix')
    def str_remove_suffix(s: str, suffix: str):
        return s[len(suffix):] if s.endswith(suffix) else s


class ezstrkit:
    @staticmethod
    def to_columns(items: T.Iterable, total_max_width, *, horizontal=False, sep=' '):
        """convert items into a single `str` in columns"""
        items = [s for s in items]
        num = len(items)
        max_len = max([ezstr.get_width(s) for s in items])
        col_w = max_len + ezstr.get_width(sep)
        col_w_max = total_max_width // col_w or 1
        row_n = num // col_w_max + bool(num % col_w_max)
        if horizontal:
            rows = [items[i:i + col_w_max] for i in range(0, num, col_w_max)]
        else:
            rows = [items[i::row_n] for i in range(0, row_n)]
        lines_l = [sep.join([f'{s}{" " * (max_len - ezstr.get_width(s))}' for s in row]) for row in rows]
        return '\n'.join(lines_l)
