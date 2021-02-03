#!/usr/bin/env python3
# encoding=utf8
import unicodedata

import regex

from .text_lite import *

assert ATTENTION_DO_NO_USE_THIS


def remove_accent_chars_regex(x: str):
    return regex.sub(r'\p{Mn}', '', unicodedata.normalize('NFKD', x))