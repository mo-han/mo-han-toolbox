#!/usr/bin/env python3
# encoding=utf8

from .text import regex_find


def find_url_in_text(text: str) -> list:
    prefix = 'https://www.pornhub.com'
    tmp = []
    tmp.extend(regex_find(r'/view_video\.php\?viewkey=ph[0-9a-f]+', text, dedup=True))
    tmp.extend(regex_find(r'/view_video\.php\?viewkey=\d+', text, dedup=True))
    return [prefix + e for e in tmp]
