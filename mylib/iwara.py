#!/usr/bin/env python3
# encoding=utf8
from abc import ABCMeta

import youtube_dl.extractor.iwara

from .text import regex_find
from .web import get_html_element_tree


def find_url_in_text(text: str) -> list:
    prefix = 'https://iwara.tv'
    pattern = '/videos/[0-9a-z]+'
    urls = [prefix + e for e in regex_find(pattern, text, dedup=True) if 'thumbnail' not in e]
    return urls


class IwaraXYTDL(youtube_dl.extractor.iwara.IwaraIE, metaclass=ABCMeta):
    def _real_extract(self, url):
        data = super(IwaraXYTDL, self)._real_extract(url)
        try:
            html = get_html_element_tree(url)
            uploader = html.xpath('//div[@class="node-info"]//div[@class="submitted"]//a[@class="username"]')[0].text
            data['uploader'] = uploader
            # print('#', 'uploader:', uploader)
        except IndexError:
            pass
        return data


def youtube_dl_main_x_iwara(argv=None):
    youtube_dl.extractor.IwaraIE = IwaraXYTDL
    youtube_dl.main(argv)
