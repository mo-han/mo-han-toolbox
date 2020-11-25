#!/usr/bin/env python3
# encoding=utf8
from abc import ABCMeta

import youtube_dl.extractor.iwara

from .text_ez import regex_find, ellipt_end
from .web_client import get_html_element_tree
from .fs import safe_name


def find_url_in_text(text: str) -> list:
    prefix = 'https://iwara.tv'
    pattern = '/videos/[0-9a-z]+'
    urls = [prefix + e for e in regex_find(pattern, text, dedup=True) if 'thumbnail' not in e]
    return urls


class IwaraIE(youtube_dl.extractor.iwara.IwaraIE, metaclass=ABCMeta):
    def _real_extract(self, url):
        data = super()._real_extract(url)
        try:
            html = get_html_element_tree(url)
            uploader = html.xpath('//div[@class="node-info"]//div[@class="submitted"]//a[@class="username"]')[0].text
            data['uploader'] = uploader
            # print('#', 'uploader:', uploader)
        except IndexError:
            pass
        return data
