#!/usr/bin/env python3
from logging import *
from logging import config

FMT_MESSAGE_ONLY = '%(message)s'
FMT_LEVEL1_MESSAGE_ONLY = '%(levelname).1s: %(message)s'
FMT_LEVEL1_NO_TIME = '%(levelname).1s|%(name)s: %(message)s'
FMT_LEVEL1_DATE_TIME = '%(levelname).1s|%(asctime).19s|%(name)s: %(message)s'
FMT_LEVEL1_DATE_TIME_ZONE = '%(levelname).1s|%(asctime)s|%(name)s: %(message)s'

DTFMT_ISO = '%Y-%m-%d %H:%M:%S'
DTFMT_ISO_Z = '%Y-%m-%d %H:%M:%S%z'


class LoggerKit:
    def set_all_handlers_format(self: Logger, fmt=None, date_fmt=None):
        if not fmt and not date_fmt and hasattr(self, 'formatter'):
            formatter = self.formatter
        else:
            formatter = Formatter(fmt=fmt, datefmt=date_fmt)
        for h in self.handlers:
            h.setFormatter(formatter)
        return self

    def set_all_handlers_level(self: Logger, level):
        self.setLevel(level)
        for h in self.handlers:
            h.setLevel(level)
        return self

    def add_handlers(self: Logger, *handlers):
        for h in handlers:
            self.addHandler(h)
        return self


class LoggerMixin:
    __logger_name__ = None

    @property
    def __logger__(self):
        return self.__dict__.setdefault(
            '__logger__', getLogger(self.__logger_name__ or f'{self.__module__}.{self.__class__.__name__}'))


def dict_config(d: dict, only_new=False, incremental=False):
    d = d.copy()
    d.update(disable_existing_loggers=only_new, incremental=incremental)
    config.dictConfig(d)


def init_root(fmt=FMT_LEVEL1_NO_TIME, dtfmt=DTFMT_ISO, **kwargs):
    basicConfig(format=fmt, datefmt=dtfmt)


def set_root_level(level):
    d = dict(version=1, root=dict(level=level))
    dict_config(d, only_new=False, incremental=True)


def get_logger(name, suffix=None):
    if suffix:
        name = f'{name}.{suffix}'
    return getLogger(name)
