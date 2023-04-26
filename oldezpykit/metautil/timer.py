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


class Stopwatch:
    t0: float

    class NotStarted(Exception):
        pass

    def __init__(self):
        self.results = []

    def start(self):
        self.t0 = perf_counter()
        return self

    def _check_t0(self):
        try:
            self.t0
        except AttributeError:
            raise self.NotStarted

    def stop(self):
        t1 = perf_counter()
        self._check_t0()
        td = t1 - self.t0
        self.results.append(td)
        return td

    def clear(self):
        del self.t0
        return self
