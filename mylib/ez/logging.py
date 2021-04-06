#!/usr/bin/env python3
# encoding=utf8
from logging import *

# logging format
LOG_FMT_MESSAGE_ONLY = '%(message)s'
LOG_FMT_1LEVEL_MESSAGE_ONLY = '[%(levelname).1s] %(message)s'
LOG_FMT_1LEVEL_NO_TIME = '[%(levelname).1s][%(name)s] %(message)s'
LOG_FMT_1LEVEL_DATE_TIME = '[%(levelname).1s][%(asctime).19s][%(name)s] %(message)s'
LOG_FMT_1LEVEL_DATE_TIME_ZONE = '[%(levelname).1s][%(asctime)s][%(name)s] %(message)s'
# logging datetime format
LOG_DATE_FMT_SEC = '%Y-%m-%d %H:%M:%S'
LOG_DATE_FMT_SEC_ZONE = '%Y-%m-%d %H:%M:%S%z'

LOG_FMT = LOG_FMT_1LEVEL_NO_TIME
LOG_DATE_FMT = LOG_DATE_FMT_SEC_ZONE


def get_logger(logger_name: str, level: str = 'INFO', fmt=LOG_FMT, date_fmt=LOG_DATE_FMT, handlers_l: list = None):
    formatter = Formatter(fmt=fmt, datefmt=date_fmt)
    logger = getLogger(logger_name)
    logger.setLevel(level)
    if not handlers_l:
        handlers_l = [StreamHandler()]
    for h in handlers_l:
        h.setFormatter(formatter)
        # logger.addHandler(h)
    logger.handlers = handlers_l
    return logger


def set_logger_format(logger: Logger, fmt, date_fmt):
    formatter = Formatter(fmt=fmt, datefmt=date_fmt)
    for h in logger.handlers:
        h.setFormatter(formatter)


def set_logger_level(logger: Logger, level):
    logger.setLevel(level)
    for h in logger.handlers:
        h.setLevel(level)
