#!/usr/bin/env python

import sys
import signal

LOG_FMT_MESSAGE_ONLY = '%(message)s'
LOG_FMT_SHORT_LEVEL_SHORT_TIME_NAME = '[%(levelname).1s %(asctime).19s] [%(name)s] %(message)s'
LOG_FMT_SHORT_LEVEL_TIME_NAME = '[%(levelname).1s %(asctime)s] [%(name)s] %(message)s'
LOG_DATETIME_SEC = '%Y-%m-%d %H:%M:%s'
LOG_FMT = LOG_FMT_SHORT_LEVEL_TIME_NAME
LOG_DTF = LOG_DATETIME_SEC


def win32_ctrl_c():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # %ERRORLEVEL% = '-1073741510'


class ExitCode:
    # http://www.febooti.com/products/automation-workshop/online-help/events/run-dos-cmd-command/exit-codes/
    # http://tldp.org/LDP/abs/html/exitcodes.html
    CTRL_C = 0xC000013A - 2 ** 32 if sys.platform == 'win32' else 128 + 2
    pass
