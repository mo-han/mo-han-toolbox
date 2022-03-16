#!/usr/bin/env python3
from urllib.parse import *


def tolerant_urlparse(url: str):
    r = urlparse(url)
    if not r.scheme and not r.netloc:
        r = urlparse('scheme://' + url)
    return r


def replace(named_tuple, *args, **kwargs):
    return named_tuple._replace(*args, **kwargs)
