#!/usr/bin/env python3
from threading import *


def ez_thread_factory(group=None, name=None, daemon=None):
    def new_thread(target, *args, **kwargs):
        return Thread(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)

    return new_thread
