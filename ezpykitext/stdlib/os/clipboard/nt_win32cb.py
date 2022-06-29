#!/usr/bin/env python3
import contextlib
import functools
import random
import time

from ezpykitext.extlib.win32clipboard import *


@contextlib.contextmanager
def ctx_open_win32clipboard():
    is_opened = False
    while not is_opened:
        try:
            OpenClipboard(0)
        except Exception as e:
            n = e.winerror
            if n == 5:
                time.sleep(random.random() / 100)
            elif n in (0, 1418):
                pass
            else:
                raise
        else:
            yield
            is_opened = True
        finally:
            CloseClipboard()


def deco_ctx_open_win32clipboard(target):
    @functools.wraps(target)
    def tgt(*args, **kwargs):
        with ctx_open_win32clipboard():
            return target(*args, **kwargs)

    return tgt
