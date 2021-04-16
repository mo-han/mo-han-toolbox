#!/usr/bin/env python3
import regex

from mylib.ez.text import *


def remove_accent_chars_regex(x: str):
    return regex.sub(r'\p{Mn}', '', unicodedata.normalize('NFKD', x))
