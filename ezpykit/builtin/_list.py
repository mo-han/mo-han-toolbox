#!/usr/bin/env python3
from ezpykit.metautil import typing as T


class ezlist(list, T.Generic[T.T]):
    def append_dedup(self, x, reindex=False):
        if x in self:
            if reindex:
                self.remove_all(x)
                self.append(x)
        else:
            self.append(x)

    def remove_all(self, x):
        i = 0
        while True:
            try:
                if self[i] == x:
                    del self[i]
                else:
                    i += 1
            except IndexError:
                break

    def get(self, index, default=None):
        try:
            return self[index]
        except IndexError:
            return default

    def get_first(self, default=None):
        return ezlist.get(self, 0, default=default)

    def get_last(self, default=None):
        return ezlist.get(self, -1, default=default)

    @property
    def first(self):
        return self.get_first()

    @property
    def last(self):
        return self.get_last()

    def ichunks(self: T.Iterable[T.T], n):
        r = []
        for e in self:
            r.append(e)
            if len(r) == n:
                yield r
                r = []
        yield r
