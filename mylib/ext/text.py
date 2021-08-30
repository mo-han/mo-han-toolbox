#!/usr/bin/env python3
from mylib.easy.text import *


def __ref():
    return


def remove_accent_chars_regex(x: str):
    import regex
    return regex.sub(r'\p{Mn}', '', unicodedata.normalize('NFKD', x))
