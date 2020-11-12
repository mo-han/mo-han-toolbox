#!/usr/bin/env python3
# encoding=utf8
import shutil
import sys
from typing import List

from .text import VisualLengthString
from .tricks import constrain_value


def get_terminal_width():
    return shutil.get_terminal_size()[0]


class LinePrinter:
    def __init__(self, width: int = 0, output=sys.stdout):
        self.output = output
        self.width = constrain_value(width, int, 'x > 0', True, 0)

    def print(self, text: str = '', **kwargs):
        print(text, file=self.output, flush=True, **kwargs)

    p = print

    def clear(self):
        self.line(char=' ', end='\r')

    def line(self, char: str = '-', shorter: int = 1, **kwargs):
        width = self.width or get_terminal_width()
        self.print(char * (width - shorter), **kwargs)

    l = line

    def underscore(self, **kwargs):
        self.line(char='_')

    u = underscore

    def double_line(self, **kwargs):
        self.line(char='=')

    d = double_line

    def wave_line(self, **kwargs):
        self.line(char='~')

    w = wave_line


def choose_prompt_number(choices):
    ...
