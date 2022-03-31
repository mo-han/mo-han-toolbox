#!/usr/bin/env python3
import sys

from ezpykit.allinone import *
from ezpykitext.stdlib import os

__logger__ = logging.getLogger(__name__)


def iter_path(source=None, clipboard_as_default=True, exist_first=True, use_pipe=True, recursive_glob=True):
    if clipboard_as_default and not source:
        yield from os.clpb.get_path()
        return
    if use_pipe and source == '-':
        yield from iter_path(sys.stdin.read().splitlines())
        return
    if os.clpb.check_uri(source):
        x = os.clpb.uri_api(source)
        if not x:
            return
        if isinstance(x, (list, str)):
            yield from iter_path(x)
        else:
            raise NotImplementedError('clipboard return type', type(x))
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
                yield from glob.iglob_url(s, recursive=recursive_glob)
            if exist_first and os.path_exists(s):
                yield s
            else:
                __logger__.debug('default iglob')
                yield from glob.iglob(s, recursive=recursive_glob)


def get_from_source(source=None, clipboard_as_default=True, use_pipe=True):
    if clipboard_as_default and not source:
        return os.clpb.get()
    if use_pipe and source == '-':
        return sys.stdin.read()
    if os.clpb.check_uri(source):
        return os.clpb.uri_api(source)
    return str(source)


def give_to_sink(x, sink=None, clipboard_as_default=True, use_pipe=True):
    if clipboard_as_default and not sink:
        os.clpb.set(x)
    if use_pipe and sink=='-':
        sys.stdout.write(x)
    if os.clpb.check_uri(sink):
        os.clpb.uri_api(sink, x)
