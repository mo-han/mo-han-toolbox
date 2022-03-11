#!/usr/bin/env python3
from ezpykit.stdlib.argparse import *
from mylib.easy import *
from mylib.ext import fstk, text, ostk

___ref = fstk, text, ArgumentParserWrapper

PathSourceTypeTuple = list, str, T.NoneType
PathSourceType = T.Union[T.List[str], str, T.NoneType]

stderr_print = functools.partial(print, file=sys.stderr)


def resolve_path_to_dirs_files(x: PathSourceType, *,
                               use_clipboard=True, use_stdin=False,
                               glob_recurse=False, exist_prior_to_glob=True):
    if not isinstance(x, PathSourceTypeTuple):
        raise TypeError('x', PathSourceType, type(x), x)

    if not x:
        if use_clipboard:
            xl = ostk.clipboard.list_path()
        else:
            return [], []
    elif use_stdin and x in ('-', ['-']):
        xl = sys.stdin.read().splitlines()
    else:
        if isinstance(x, list):
            xl = x
        else:
            xl = [x]
    return glob_or_exist_to_dirs_files(xl, glob_recurse=glob_recurse, exist_prior_to_glob=exist_prior_to_glob)


class ConsolePrinter:
    def __init__(self, file=sys.stdout):
        self.file = file

    @property
    def width(self):
        return shutil.get_terminal_size()[0]

    def split_line(self, char='-'):
        print(char * (self.width - 1), file=self.file)

    ll = split_line

    def clear_line(self, mask_char=' '):
        print(f'\r{mask_char * (self.width - 1)}\r', end='', file=self.file)

    cl = clear_line

    def in_line(self, *args, cursor_at_end=True):
        self.clear_line()
        if cursor_at_end:
            print(*args, end='', file=self.file, flush=True)
        else:
            print(*args, end='\r', file=self.file)

    il = in_line

    def new_line(self):
        print('', file=self.file)

    nl = new_line
