#!/usr/bin/env python3
from ezpykit.allinone import *
from ezpykitext.stdlib import os


def isrcpath(source, clipboard_path_as_default=True, exist_first=True):
    try:
        x = os.clpb.url_api(str(source))
    except NotImplementedError:
        pass
    except ValueError as e:
        if e.args[0] == 'invalid scheme':
            pass
    else:
        if not x:
            return
        if isinstance(x, list):
            yield from x
        elif isinstance(x, str):
            yield x
        else:
            raise NotImplementedError('result type', type(x))
        return

    if not source:
        yield from os.clpb.get_path()
        return
    if isinstance(source, str):
        source = [source]
    if isinstance(source, T.Iterable):
        for s in source:
            if not isinstance(s, str):
                s = str(s)
            if s.startswith('glob://'):
                yield from glob.iglob_url(s, recursive=True)
            if exist_first and os.path_exists(s):
                yield s
            else:
                yield from glob.iglob(s, recursive=True)
