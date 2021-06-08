#!/usr/bin/env python3
from abc import ABCMeta
from urllib.parse import urlparse, urlunparse

import youtube_dl.extractor.iwara as ytdl_iwara

from mylib.easy.text import regex_find
from mylib.ex.html import *
from mylib.web_client import get_html_element_tree

HE = lxml.html.HtmlElement


def find_url_in_text(text: str) -> list:
    prefix = 'https://iwara.tv'
    pattern = '/videos/[0-9a-zA-Z]+'
    urls = [prefix + e for e in regex_find(pattern, text, dedup=True) if 'thumbnail' not in e]
    return urls


# ytdl_iwara.InfoExtractor = youtube_dl_x.ytdl_common.InfoExtractor  # SEEMINGLY NO EFFECT


class IwaraIE(ytdl_iwara.IwaraIE, metaclass=ABCMeta):
    def _real_extract(self, url):
        data = super()._real_extract(url)
        # youtube_dl_x.safe_title(data)
        try:
            html = get_html_element_tree(url)
            uploader = html.xpath('//div[@class="node-info"]//div[@class="submitted"]//a[@class="username"]')[0].text
            data['uploader'] = uploader
            # print('#', 'uploader:', uploader)
        except IndexError:
            pass
        return data


def iter_all_video_url_of_user(who: str, ecchi=True, only_urls=False):
    m = re.match(r'.*iwara\.tv/users/(.+)/?', who)
    if m:
        who = m.group(1)
    domain = 'ecchi.iwara.tv' if ecchi else 'iwara.tv'
    url = f'https://{domain}/users/{who}/videos?language=en'
    end = False

    while not end:
        r = call_factory_retry(requests.get)(url)
        h = HTMLResponseParser(r).check_ok_or_raise().get_html_element()
        for e in h.cssselect('.field-item a'):
            href = e.attrib['href']
            img_d = e.find('img').attrib
            thumbnail = img_d['src']
            title = img_d['title']
            url = f'https://{domain}{href}'
            url_pr = urlparse(url)
            url = urlunparse((url_pr.scheme, url_pr.netloc, url_pr.path, '', '', ''))
            if only_urls:
                yield url
            else:
                yield {'title': title, 'url': url, 'thumbnail': thumbnail}
        find_next = h.cssselect('.pager-next a')
        if find_next:
            next = find_next[-1]
            url = f'https://{domain}{next.attrib["href"]}'
        else:
            end = True


def find_video_id_in_link(link: str):
    return re.match(r'.*/videos/([0-9a-z]+)', link).group(1)
