#!/usr/bin/env python3
from contextlib import contextmanager

from ezpykit.stdlib.logging import LoggerMixin


class ContractorError(Exception):
    pass


class Failure(ContractorError):
    errors: list

    def __init__(self, contractor_method=None, *args, **kwargs):
        self.errors = []
        super().__init__((contractor_method, args, kwargs), self.errors)


class Abortion(ContractorError):
    pass


class Contractor(LoggerMixin):
    def __init__(self, *children: 'Contractor'):
        self.children = children

    def _iter_do_self(self, e: Failure, what, *args, **kwargs):
        name = f'{self.do.__name__}_{what}'
        m = getattr(self, name, None)
        if callable(m):
            try:
                yield m(*args, **kwargs)
            except Abortion:
                raise
            except Exception as error:
                e.errors.append(error)
        else:
            self.__logger__.debug(f'{name} is not a valid method for {self}')

    def _iter_do_children(self, e: Failure, what, *args, **kwargs):
        for c in self.children:
            try:
                yield c.do(what, *args, **kwargs)
            except Abortion:
                raise
            except Exception as error:
                e.errors.append(error)

    def do(self, what, *args, **kwargs):
        e = Failure(self.do, what, *args, **kwargs)
        for r in self._iter_do_self(e, what, *args, **kwargs):
            return r
        for r in self._iter_do_children(e, what, *args, **kwargs):
            return r
        raise e

    def get(self, default, what, *args, **kwargs):
        try:
            return self.do(what, *args, **kwargs)
        except (Failure, Abortion):
            return default
