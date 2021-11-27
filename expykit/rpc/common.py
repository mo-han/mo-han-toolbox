#!/usr/bin/env python3
import json
import threading

from functools import lru_cache

__ref_import = json, threading, lru_cache


class RPCError(Exception):
    pass


def test_hello(x):
    print(x)
    return x
