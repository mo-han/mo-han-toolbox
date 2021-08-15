#!/usr/bin/env python3
from datetime import *


def ez_convert_time_obj_to_time_delta(time_obj: time):
    return datetime.combine(date.min, time_obj) - datetime.min


def ez_convert_time_delta_to_time_obj(time_delta: timedelta):
    return (datetime.min + time_delta).time()
