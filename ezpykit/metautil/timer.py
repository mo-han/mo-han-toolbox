#!/usr/bin/env python3
from time import perf_counter, sleep
from contextlib import contextmanager


@contextmanager
def ctx_ensure_min_time_duration(t):
    t0 = perf_counter()
    yield
    td = perf_counter() - t0
    if td < t:
        sleep(t - td)
