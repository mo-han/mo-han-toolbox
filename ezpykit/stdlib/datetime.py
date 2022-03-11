#!/usr/bin/env python3
from datetime import time, datetime, date, timedelta


def datetime_to_delta(time_obj: time):
    return datetime.combine(date.min, time_obj) - datetime.min


def delta_to_datetime(time_delta: timedelta):
    return (datetime.min + time_delta).time()
