#!/usr/bin/env python3
# encoding=utf8
import shutil

from .tricks import constrain_value


class SimpleDrawer:
    def __init__(self, width: int = 0, print_method=print, print_end=''):
        self._print = print_method
        self.end = print_end
        self.width = constrain_value(width, int, 'x > 0', True, 0)

    def print(self, text: str, **kwargs):
        end = kwargs.pop('end', None) or self.end
        return self._print(text + end, **kwargs)

    def horizontal_line(self, char: str = '-', **kwargs):
        width = self.width or shutil.get_terminal_size()[0] - 1
        return self.print(char * width, **kwargs)

    hl = horizontal_line

    def horizontal_line_under(self, **kwargs):
        return self.horizontal_line(char='_')

    hlu = horizontal_line_under

    def horizontal_line_double(self, **kwargs):
        return self.horizontal_line(char='=')

    hld = horizontal_line_double

    def horizontal_line_wave(self, **kwargs):
        return self.horizontal_line(char='~')

    hlw = horizontal_line_wave
