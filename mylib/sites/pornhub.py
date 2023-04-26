#!/usr/bin/env python3
from abc import ABCMeta

import youtube_dl.extractor.pornhub as ytdl_pornhub

from mylib.easy import text
from mylib.web_client import get_html_element_tree


def find_url_in_text(x: str) -> list:
    prefix = 'https://www.pornhub.com'
    pattern = r'/view_video\.php\?viewkey=(?:ph[0-9a-f]+|[0-9a-f]+)'
    return [prefix + e for e in text.regex_find(pattern, x, dedup=True)]


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
