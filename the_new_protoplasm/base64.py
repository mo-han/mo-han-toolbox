#!/usr/bin/env python3
import base64
import binascii


def decode_base64_string_to_bytes(s: str):
    try:
        return base64.b64decode(s)
    except binascii.Error as e:
        if e.args == ('Incorrect padding',):
            return decode_base64_string_to_bytes(s + '=')
        else:
            raise e
