#!/usr/bin/env python
import argparse
import logging
import os
import random
import signal
import string
import sys
import tempfile

from lib_math import is_power_of_2_int

# logging format
LOG_FMT_MESSAGE_ONLY = '%(message)s'
LOG_FMT_SINGLE_LEVEL_SHORT_TIME_NAME = '[%(levelname).1s][%(asctime).19s][%(name)s] %(message)s'
LOG_FMT_SINGLE_LEVEL_TIME_NAME = '[%(levelname).1s][%(asctime)s][%(name)s] %(message)s'
LOG_FMT = LOG_FMT_SINGLE_LEVEL_TIME_NAME
# logging datetime format
LOG_DTF_SEC = '%Y-%m-%dT%H:%M:%S'
LOG_DTF_SEC_ZONE = '%Y-%m-%dT%H:%M:%S%z'
LOG_DTF = LOG_DTF_SEC_ZONE

CHARS_ALPHANUMERIC = string.ascii_letters + string.digits

TEMPDIR = tempfile.gettempdir()
ILLEGAL_CHARS = ['\\', '/', ':', '*', '"', '<', '>', '|', '?']


class VoidDuck:
    """a void, versatile, useless and quiet duck, called in any way, return nothing, raise nothing"""
    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False


def str_ishex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


class ArgumentParserCompactOptionHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            # noinspection PyProtectedMember
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(action.option_strings) + ' ' + args_string


def arg_type_pow2(x):
    i = int(x)
    if is_power_of_2_int(i):
        return i
    else:
        raise argparse.ArgumentTypeError("'{}' is not power of 2".format(x))


def arg_type_range_factory(x_type, x_range_condition: str):
    def arg_type_range(xx):
        x = x_type(xx)
        if eval(x_range_condition):
            return x
        else:
            raise argparse.ArgumentTypeError("'{}' not in range {}".format(xx, x_range_condition))

    return arg_type_range


def percentage(quotient, digits: int = 1) -> str:
    fmt = '{:.' + str(digits) + '%}'
    return fmt.format(quotient)


def new_logger(logger_name: str, level: str = 'INFO', fmt=LOG_FMT, datetime_fmt=LOG_DTF, handlers_l: list = None):
    formatter = logging.Formatter(fmt=fmt, datefmt=datetime_fmt)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    if not handlers_l:
        handlers_l = [logging.StreamHandler()]
    for h in handlers_l:
        h.setFormatter(formatter)
        logger.addHandler(h)
    return logger


try:
    from msvcrt import getch
except ImportError:
    import sys
    import tty
    import termios


    def getch():
        """
        Gets a single character from STDIO.
        """
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def random_fname(prefix: str = '', suffix: str = '', length: int = 8):
    fname = prefix + ''.join(random.sample(CHARS_ALPHANUMERIC, length)) + suffix
    return fname if not os.path.exists(fname) else random_fname(prefix=prefix, suffix=suffix, length=length)


def safe_basename(s: str):
    p = s
    for i in ILLEGAL_CHARS:
        p = p.replace(i, ' ')
    return p


def safe_print(s):
    s = str(s)
    try:
        print(s)
    except UnicodeEncodeError:
        for c in s:
            try:
                print(c, end='')
            except UnicodeEncodeError:
                pass
        else:
            print()


def win32_ctrl_c():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'


def rectify_basename(s: str, replace: bool = True):
    char_map = {
        '\\': '⧹',  # U+29F9 (big reverse solidus)
        '/': '⧸',  # U+29F8 (big solidus, permitted in Windows file and folder names）
        '|': '￨',  # U+FFE8 (halfwidth forms light vertical)
        ':': '꞉',  # U+A789 (modifier letter colon, sometimes used in Windows filenames)
        '*': '∗',  # U+2217 (asterisk operator)
        '?': '？',  # U+FF1F (full-width question mark)
        '"': '″',  # U+2033 (DOUBLE PRIME)
        '<': '﹤',  # U+FE64 (small less-than sign)
        '>': '﹥',  # U+FE65 (small greater-than sign)
        '\t': '',
        '\r': '',
        '\n': '',
        '&amp;': '&',
    }
    if replace:
        for k, v in char_map.items():
            s = s.replace(k, v)
    else:
        for k in char_map:
            s = s.replace(k, '')
    return s


class ExitCode:
    # http://www.febooti.com/products/automation-workshop/online-help/events/run-dos-cmd-command/exit-codes/
    # http://tldp.org/LDP/abs/html/exitcodes.html
    CTRL_C = 0xC000013A - 2 ** 32 if sys.platform == 'win32' else 128 + 2
    pass
