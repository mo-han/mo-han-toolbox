#!/usr/bin/env python3
# encoding=utf8
from logging import *
from logging.handlers import *

# logging format
LOG_FMT_MESSAGE_ONLY = '%(message)s'
LOG_FMT_1LEVEL_MESSAGE_ONLY = '[%(levelname).1s] %(message)s'
LOG_FMT_1LEVEL_NO_TIME = '[%(levelname).1s][%(name)s] %(message)s'
LOG_FMT_1LEVEL_DATE_TIME = '[%(levelname).1s][%(asctime).19s][%(name)s] %(message)s'
LOG_FMT_1LEVEL_DATE_TIME_ZONE = '[%(levelname).1s][%(asctime)s][%(name)s] %(message)s'
# logging datetime format
LOG_DATE_FMT_SEC = '%Y-%m-%d %H:%M:%S'
LOG_DATE_FMT_SEC_ZONE = '%Y-%m-%d %H:%M:%S%z'


class EzLogger(Logger):
    def set_all_handlers_format(self, fmt=None, date_fmt=None):
        if not fmt and not date_fmt and hasattr(self, 'formatter'):
            formatter = self.formatter
        else:
            formatter = Formatter(fmt=fmt, datefmt=date_fmt)
        for h in self.handlers:
            h.setFormatter(formatter)
        return self

    def set_all_handlers_level(self, level):
        self.setLevel(level)
        for h in self.handlers:
            h.setLevel(level)
        return self

    def add_handlers(self, *handlers):
        for h in handlers:
            self.addHandler(h)
        return self


class EzLoggingMixin:
    @property
    def __logger__(self):
        try:
            r = self.__self_logger
        except AttributeError:
            r = self.__self_logger = ez_get_logger(f'{self.__class__.__name__}', 'DEBUG')
        finally:
            return r


def ez_get_logger(logger_name: str, level: str = 'INFO', fmt=LOG_FMT_1LEVEL_NO_TIME, date_fmt=LOG_DATE_FMT_SEC_ZONE,
                  handlers: list = None) -> EzLogger:
    formatter = Formatter(fmt=fmt, datefmt=date_fmt)
    logger = getLogger(logger_name)
    logger.setLevel(level)
    if not handlers:
        handlers = [StreamHandler()]
    for h in handlers:
        h.setFormatter(formatter)
    logger.handlers = handlers
    logger.__class__ = EzLogger
    logger.formatter = formatter
    return logger
