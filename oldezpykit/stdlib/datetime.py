#!/usr/bin/env python3
from datetime import *
import re


def datetime_to_delta(time_obj: time):
    return datetime.combine(date.min, time_obj) - datetime.min


def delta_to_datetime(time_delta: timedelta):
    return (datetime.min + time_delta).time()


def from_iso_format(s):
    yr, mon, day, h, m, s, ss, tzs, tzh, tzm = re.match(
        r'(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(\.\d+)?([+-])?(\d{2})?:?(\d{2})?', s).groups()
    tzs = int((tzs or '') + '1')
    tzh = int(tzh or 0) * tzs
    tzm = int(tzm or 0) * tzs
    if tzh or tzm:
        tz = timezone(timedelta(hours=tzh, minutes=tzm))
    else:
        tz = timezone.utc
    new: datetime = datetime.min
    new = new.replace(year=int(yr), month=int(mon), day=int(day), hour=int(h), minute=int(m), second=int(s),
                      microsecond=int(float(ss or 0) * 1000000), tzinfo=tz)
    return new
