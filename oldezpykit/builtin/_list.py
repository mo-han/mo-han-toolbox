#!/usr/bin/env python3
from oldezpykit.metautil import typing as T


class ezlist(list, T.Generic[T.T]):
    current_index = 0

    def to_dict(self):
        d = {}
        for i, e in enumerate(self):
            d[i] = e
        return d

    @property
    def current(self):
        return self.get(self.current_index)

    @property
    def next(self):
        self.current_index += 1
        total = len(self)
        if self.current_index >= total:
            self.current_index -= total
        return self.current

    @property
    def previous(self):
        self.current_index -= 1
        total = len(self)
        if self.current_index <= - total:
            self.current_index += total * 2
        return self.current

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

    @first.setter
    def first(self, value):
        self[0] = value

    @property
    def last(self):
        return self.get_last()

    @last.setter
    def last(self, value):
        self[-1] = value

    def iter_chunks(self: T.Iterable[T.T], n):
        r = []
        for e in self:
            r.append(e)
            if len(r) == n:
                yield r
                r = []
        yield r
