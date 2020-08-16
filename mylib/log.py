#!/usr/bin/env python3
# encoding=utf8
import logging

# logging format
LOG_FMT_MESSAGE_ONLY = '%(message)s'
LOG_FMT_1LEVEL_MESSAGE_ONLY = '[%(levelname).1s] %(message)s'
LOG_FMT_1LEVEL_NO_TIME = '[%(levelname).1s][%(name)s] %(message)s'
LOG_FMT_1LEVEL_DATE_TIME = '[%(levelname).1s][%(asctime).19s][%(name)s] %(message)s'
LOG_FMT_1LEVEL_DATE_TIME_ZONE = '[%(levelname).1s][%(asctime)s][%(name)s] %(message)s'
# logging datetime format
LOG_DTF_SEC = '%Y-%m-%dT%H:%M:%S'
LOG_DTF_SEC_ZONE = '%Y-%m-%dT%H:%M:%S%z'

LOG_FMT = LOG_FMT_1LEVEL_NO_TIME
LOG_DTF = LOG_DTF_SEC_ZONE


def get_logger(logger_name: str, level: str = 'INFO', fmt=LOG_FMT, datetime_fmt=LOG_DTF, handlers_l: list = None):
    formatter = logging.Formatter(fmt=fmt, datefmt=datetime_fmt)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    if not handlers_l:
        handlers_l = [logging.StreamHandler()]
    for h in handlers_l:
        h.setFormatter(formatter)
        logger.addHandler(h)
    return logger
