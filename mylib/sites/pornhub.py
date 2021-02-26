#!/usr/bin/env python3
# encoding=utf8
from abc import ABCMeta

import youtube_dl.extractor.pornhub as ytdl_pornhub

from mylib.text import regex_find
from mylib.web_client import get_html_element_tree


def find_url_in_text(text: str) -> list:
    prefix = 'https://www.pornhub.com'
    pattern = r'/view_video\.php\?viewkey=(?:ph[0-9a-f]+|\d+)'
    return [prefix + e for e in regex_find(pattern, text, dedup=True)]


# ytdl_pornhub.InfoExtractor = youtube_dl_x.ytdl_common.InfoExtractor  # SEEMINGLY NO EFFECT


class PornHubIE(ytdl_pornhub.PornHubIE, metaclass=ABCMeta):
    def _real_extract(self, url):
        data = super()._real_extract(url)
        # youtube_dl_x.safe_title(data)
        try:
            if data.get('uploader'):
                return data
            html = get_html_element_tree(url)
            uploader = html.xpath('//div[@class="userInfo"]//a')[0].text
            data['uploader'] = uploader
            # print('#', 'uploader:', uploader)
        except IndexError:
            pass
        return data
