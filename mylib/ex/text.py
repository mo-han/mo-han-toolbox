#!/usr/bin/env python3
import regex
import textdistance

from mylib.easy.text import *


def __ref():
    return textdistance


def remove_accent_chars_regex(x: str):
    return regex.sub(r'\p{Mn}', '', unicodedata.normalize('NFKD', x))
