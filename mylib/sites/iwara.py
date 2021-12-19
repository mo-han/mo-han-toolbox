#!/usr/bin/env python3
import warnings
from abc import ABCMeta
from urllib.parse import urlparse, urlunparse

import youtube_dl.extractor.iwara as ytdl_iwara

from ezpykit import *
from mylib import easy
from mylib.easy import text
from mylib.ext import html
from mylib.web_client import get_html_element_tree

HE = html.lxml_html.HtmlElement

regex = easy.re


def find_video_url_guess_path(s: str, ecchi=True) -> list:
    prefix = 'https://ecchi.iwara.tv' if ecchi else 'https://www.iwara.tv'
    pattern = '/videos/[0-9a-zA-Z]+'
    urls = [prefix + e for e in text.regex_find(pattern, s, dedup=True) if 'thumbnail' not in e]
    return urls


def find_video_url(s: str):
    from ezpykit.builtin import list
    r = list()
    for i in re.findall(r'https?://.*iwara.tv/videos/[0-9a-zA-Z]+', s):
        r.append_dedup(i)
    if r:
        return r
    return find_video_url_guess_path(s)


# ytdl_iwara.InfoExtractor = youtube_dl_x.ytdl_common.InfoExtractor  # SEEMINGLY NO EFFECT


class IwaraIE(ytdl_iwara.IwaraIE, metaclass=ABCMeta):
    def _real_extract(self, url):
        data = super()._real_extract(url)
        # youtube_dl_x.safe_title(data)
        try:
            h = get_html_element_tree(url)
            uploader = h.xpath('//div[@class="node-info"]//div[@class="submitted"]//a[@class="username"]')[0].text
            data['uploader'] = uploader
            # print('#', 'uploader:', uploader)
            for v in data['formats']:
                file_url = v.get('url')
                if file_url:
                    query = easy.urllib.parse.urlparse(file_url).query
                    query_file: str = easy.urllib.parse.parse_qs(query)['file'][0]
                    filename = query_file.split('/')[-1]
                    parts = filename.split('_')
                    sn = parts[0]
                    id_ = parts[1]
                    data['id'] = f'{id_} {sn}'
                    break
        except IndexError as e:
            warnings.warn(f'{e}')
        return data


def iter_all_video_url_of_user(who: str, ecchi=True, only_urls=False):
    m = regex.match(r'.*iwara\.tv/users/(.+)/?', who)
    if m:
        who = m.group(1)
    domain = 'ecchi.iwara.tv' if ecchi else 'iwara.tv'
    url = f'https://{domain}/users/{who}/videos?language=en'
    end = False

    while not end:
        r = easy.call_factory_retry(html.requests.get)(url)
        h = html.HTMLResponseParser(r).check_ok_or_raise().get_html_element()
        title_d = {a.attrib['href']: a.text for a in h.cssselect('h3.title a')}
        for e in h.cssselect('.field-item a'):
            href = e.attrib['href']
            img_d = e.find('img').attrib
            thumbnail = img_d['src']
            title = img_d['title'] = title_d[href]
            url = f'https://{domain}{href}'
            url_pr = urlparse(url)
            url = urlunparse((url_pr.scheme, url_pr.netloc, url_pr.path, '', '', ''))
            if only_urls:
                yield url
            else:
                yield {'title': title, 'url': url, 'thumbnail': thumbnail}
        find_next = h.cssselect('.pager-next a')
        if find_next:
            go_next = find_next[-1]
            url = f'https://{domain}{go_next.attrib["href"]}'
        else:
            end = True


def find_video_id_in_link(link: str):
    return regex.match(r'.*/videos/([0-9a-z]+)', link).group(1)
