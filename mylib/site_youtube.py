#!/usr/bin/env python3
# encoding=utf8

from .text_ez import regex_find


def find_url_in_text(text: str) -> list:
    p = r'/watch\?v=[-\w]+'
    return ['https://www.youtube.com' + e for e in regex_find(p, text, dedup=True)]

