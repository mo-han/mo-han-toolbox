#!/usr/bin/env python3
# encoding=utf8
import shutil
import sys

from .tricks import constrain_value


class SimpleCLIDisplay:
    def __init__(self, width: int = 0, output=sys.stdout):
        self.output = output
        self.width = constrain_value(width, int, 'x > 0', True, 0)

    def print(self, text: str = '', **kwargs):
        return print(text, file=self.output, **kwargs)

    def horizontal_line(self, char: str = '-', shorter: int = 0, **kwargs):
        width = self.width or shutil.get_terminal_size()[0]
        return self.print(char * (width - shorter), **kwargs)

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
