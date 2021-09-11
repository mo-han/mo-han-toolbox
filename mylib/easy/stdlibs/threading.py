#!/usr/bin/env python3
from threading import *
from mylib.easy.common import T


def ez_thread_factory(group=None, name=None, daemon=None):
    def new_thread(target: T.Callable, *args, **kwargs):
        return Thread(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)

    return new_thread
