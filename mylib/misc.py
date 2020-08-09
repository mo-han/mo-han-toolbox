#!/usr/bin/env python
import os
import random
import string
import sys

# logging format
LOG_FMT_MESSAGE_ONLY = '%(message)s'
LOG_FMT_1LEVEL_NO_TIME = '[%(levelname).1s][%(name)s] %(message)s'
LOG_FMT_1LEVEL_DATE_TIME = '[%(levelname).1s][%(asctime).19s][%(name)s] %(message)s'
LOG_FMT_1LEVEL_DATE_TIME_ZONE = '[%(levelname).1s][%(asctime)s][%(name)s] %(message)s'
LOG_FMT = LOG_FMT_1LEVEL_NO_TIME
# logging datetime format
LOG_DTF_SEC = '%Y-%m-%dT%H:%M:%S'
LOG_DTF_SEC_ZONE = '%Y-%m-%dT%H:%M:%S%z'
LOG_DTF = LOG_DTF_SEC_ZONE

CHARS_ALPHANUMERIC = string.ascii_letters + string.digits

ILLEGAL_CHARS = ['\\', '/', ':', '*', '"', '<', '>', '|', '?']


def percentage(quotient, digits: int = 1) -> str:
    fmt = '{:.' + str(digits) + '%}'
    return fmt.format(quotient)


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
