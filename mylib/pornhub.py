#!/usr/bin/env python3
# encoding=utf8

from .text import regex_find


def find_url_from(text: str):
    p = r'/view_video\.php\?viewkey=ph[0-9a-f]+'
    return ['https://www.pornhub.com' + e for e in regex_find(p, text, dedup=True)]

