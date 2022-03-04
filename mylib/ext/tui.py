#!/usr/bin/env python3
import mylib.ext.tricks
from ezpykit.enhance_builtin import ezstrkit
from mylib.easy import *

CRLF = f'\r\n'


def get_terminal_width():
    return shutil.get_terminal_size()[0]


class LinePrinter:
    def __init__(self, width: int = 0, output=sys.stdout):
        self.output = output
        self.width = mylib.ext.tricks.constrained(width, int, 'x > 0', enable_default=True, default=0)

    def print(self, text: str = '', **kwargs):
        print(text, file=self.output, flush=True, **kwargs)

    p = print

    def clear_line(self):
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


def prompt_choose_number(header: str, choices, default_num: int = None, *, in_columns=True):
    choices_n = len(choices)
    choices_menu = [f'  {i + 1}) {choices[i]}' for i in range(choices_n)]
    if in_columns:
        choices_menu = ezstrkit.to_columns(choices_menu, get_terminal_width() - 2)
    else:
        choices_menu = CRLF.join(choices_menu)
    prompt_end = f' [{default_num}]: ' if default_num else ': '
    n = input(f'{header}{CRLF}{choices_menu}{CRLF}  Input 1-{choices_n}{prompt_end}') or default_num
    if n:
        try:
            i = int(n) - 1
            if i < 0:
                raise ValueError
            return choices[i]
        except (IndexError, ValueError):
            return prompt_choose_number(header, choices, default_num, in_columns=in_columns)


def prompt_choose(header: str, choices: dict, default_key=None, *, in_columns=True):
    choices_menu = [f'  {x}) {y}' for x, y in choices.items()]
    if in_columns:
        choices_menu = ezstrkit.to_columns(choices_menu, get_terminal_width() - 2)
    else:
        choices_menu = CRLF.join(choices_menu)
    input_choices = '/'.join(
        [f'[{k}]' if k == default_key else k for k in choices.keys()]
        if default_key else choices.keys())
    key = input(f'{header}{CRLF}{choices_menu}{CRLF}  Input {input_choices}: ') or default_key
    if key in choices:
        return choices[key]
    else:
        prompt_choose(header, choices, default_key, in_columns=in_columns)


def prompt_confirm(ask: str, default=None, *, yes='y', no='n'):
    d = {yes: True, no: False}
    if default is True:
        yn = f'[{yes}]/{no}'
    elif default is False:
        yn = f'{yes}/[{no}]'
    else:
        yn = f'{yes}/{no}'
    x = input(f'{ask} {yn}: ')
    if x in d:
        return d[x]
    elif not x and default in (True, False):
        return default
    else:
        return prompt_confirm(ask, default, yes=yes, no=no)


def prompt_input(header: str, default: str = None):
    x = input(header)
    if x:
        return x
    elif default is not None:
        return default
    else:
        return prompt_input(header=header, default=default)
