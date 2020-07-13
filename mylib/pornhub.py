#!/usr/bin/env python3
# encoding=utf8

from .text import regex_find


def find_url_in_text(text: str) -> list:
    prefix = 'https://www.pornhub.com'
    pattern = r'/view_video\.php\?viewkey=(?:ph[0-9a-f]+|\d+)'
    return [prefix + e for e in regex_find(pattern, text, dedup=True)]
