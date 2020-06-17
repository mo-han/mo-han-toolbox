#!/usr/bin/env python3
# encoding=utf8


class SimpleDrawer:
    LONG_LINE_LENGTH = 32
    BOX_DRAWING_CHARS = {'hl': '─', 'vl': '│'}

    def __init__(self, print_method=print, print_end=''):
        self._print = print_method
        self.end = print_end

    def print(self, text: str, **kwargs):
        end = kwargs.pop('end', None) or self.end
        return self._print(text + end, **kwargs)

    def horizontal_line(self, length=LONG_LINE_LENGTH, **kwargs):
        return self.print(self.BOX_DRAWING_CHARS['hl'] * length, **kwargs)

    hl = horizontal_line
