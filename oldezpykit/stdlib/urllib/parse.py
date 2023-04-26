#!/usr/bin/env python3
from urllib.parse import *


def tolerant_urlparse(url: str, default_prefix='scheme://'):
    if '://' not in url:
        url = default_prefix + url
    r = urlparse(url)
    # if not r.scheme and not r.netloc:
    #     r = urlparse(default_prefix + url)
    return r


def replace(named_tuple, *args, **kwargs):
    return named_tuple._replace(*args, **kwargs)
