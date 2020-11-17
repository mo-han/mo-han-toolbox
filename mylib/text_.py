#!/usr/bin/env python3
# encoding=utf8
from typing import Iterable, Iterator
from unicodedata import east_asian_width

CR = '\r'
LF = '\n'
CRLF = '\r\n'


class VisualLengthString(str):
    def __len__(self):
        n = super().__len__()
        n += sum([1 for c in self if east_asian_width(c) == 'W'])
        return n

    def __getitem__(self, item):
        return VisualLengthString(super().__getitem__(item))

    def __iter__(self):
        return (VisualLengthString(s) for s in super().__iter__())


def list2col_str(x: Iterable or Iterator, width, *, horizontal=False, sep=2):
    """transfer list items into a single `str` in format of columns"""
    vls = VisualLengthString
    sep_s = ' ' * sep
    text_l = [vls(s) for s in x]
    max_len = max([len(s) for s in text_l])
    n = len(text_l)
    col_w = max_len + sep
    col_n = width // col_w or 1
    row_n = n // col_n + bool(n % col_n)
    if horizontal:
        rows_l = [text_l[i:i + col_n] for i in range(0, n, col_n)]
    else:
        rows_l = [text_l[i::row_n] for i in range(0, row_n)]
    lines_l = [sep_s.join([f'{s}{" " * (max_len - len(s))}' for s in row]) for row in rows_l]
    return '\n'.join(lines_l)
