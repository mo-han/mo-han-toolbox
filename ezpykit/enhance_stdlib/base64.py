#!/usr/bin/env python3
from base64 import *
from base64 import _bytes_from_decode_data as bytes_from_decode_data


def tolerant_b64decode(s, altchars=None, validate=False):
    s = bytes_from_decode_data(s)
    remainder = len(s) % 4
    if remainder:
        s += b'=' * (4 - remainder)
    return b64decode(s, altchars=altchars, validate=validate)
