#!/usr/bin/env python3
from re import *


def find_words(s: str, allow_mix_non_word_chars='\''):
    if allow_mix_non_word_chars is True:
        return [p for p in s.split() if search(r'\w', p)]
    elif allow_mix_non_word_chars:
        pattern = fr'[\w{escape(allow_mix_non_word_chars)}]+'
        return [p.strip() for p in findall(pattern, s)]
    else:
        return findall(r'\w+', s)


def replace(s, pattern: str, repl: str, *, use_regex=False, ignore_case=False):
    if use_regex:
        if ignore_case:
            return sub(pattern, repl, s, flags=IGNORECASE)
        else:
            return sub(pattern, repl, s)
    else:
        if ignore_case:
            return sub(escape(pattern), escape(repl), s, flags=IGNORECASE)
        else:
            return s.replace(pattern, repl)
