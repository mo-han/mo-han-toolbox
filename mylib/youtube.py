#!/usr/bin/env python3
# encoding=utf8

from .text import regex_find


def find_url_from(text: str):
    p = r'/watch\?v=[-\w]+'
    return ['https://www.youtube.com' + e for e in regex_find(p, text, dedup=True)]

