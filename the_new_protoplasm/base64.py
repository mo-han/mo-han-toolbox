#!/usr/bin/env python3
import base64
import binascii
import logging

from . import func

__logger__ = logging.getLogger('.'.join(func.get_parent_folder_name_and_basename(__file__)))


def decode_base64_string_to_bytes(s: str):
    if '-' in s:
        return b''.join(decode_base64_string_to_bytes(i) for i in s.split('-'))
    try:
        return base64.b64decode(s)
    except binascii.Error as e:
        if e.args == ('Incorrect padding',):
            __logger__.debug(f'{e}: {s}')
            return decode_base64_string_to_bytes(s + '=')
        else:
            __logger__.debug(f'class: {e.__class__.__name__}')
            __logger__.debug(f'args: {e.args}')
            raise e
