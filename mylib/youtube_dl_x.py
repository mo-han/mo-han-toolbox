#!/usr/bin/env python3
# encoding=utf8
from abc import ABCMeta
from importlib import import_module
from pprint import pprint

import youtube_dl
import youtube_dl.extractor.xvideos
from youtube_dl.extractor import common as ytdl_common
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import sanitize_filename

from .ex import fstk
from mylib.sites.iwara import IwaraIE
from mylib.sites.pornhub import PornHubIE
from .web_client import parse_https_url, get_html_element_tree


def __unused_import_keeper():
    return pprint


# import module `youtube_dl.YoutubeDL` (forestalled by same name class `youtube_dl.YoutubeDL`)
ytdl_YoutubeDL = import_module('youtube_dl.YoutubeDL')


def limit_len_sanitize_filename(s, restricted=False, is_id=False):
    if not is_id:
        s = fstk.sanitize_xu200(s)
    return sanitize_filename(s, restricted=restricted, is_id=is_id)


def safe_title(extracted_data: dict):
    title = extracted_data['title']
    extracted_data['title'] = fstk.sanitize_xu200(title)


class NewInfoExtractor(InfoExtractor, metaclass=ABCMeta):
    """SEEMS LIKE NO EFFECT"""

    def extract(self, url):
        data = super().extract(url)
        safe_title(data)
        print(self.__class__.__name__, data['title'])


class GenericInfoExtractor(youtube_dl.extractor.GenericIE, metaclass=ABCMeta):
    def _real_extract(self, url):
        data = super()._real_extract(url)
        pr = parse_https_url(url)
        kiss_jav = 'kissjav.com'
        if pr.netloc == kiss_jav:
            for entry in data['entries']:
                entry['id'] = f'{kiss_jav} {pr.path.strip("/").split("/")[0]}'
                entry['uploader'] = get_html_element_tree(url).xpath(
                    '//div[@class="content-info" and contains(text(), "From")]//a')[0].text_content()
            # pprint(data)
        return data


class XVideosIE(youtube_dl.extractor.xvideos.XVideosIE, metaclass=ABCMeta):
    def _real_extract(self, url):
        data = super()._real_extract(url)
        vid = data['id']
        data['id'] = f'xvideos {vid}'
        ht = get_html_element_tree(url)
        try:
            data['uploader'] = ht.xpath('//span[@class="name"]')[0].text
        except IndexError:
            pass
        return data


def youtube_dl_main_x(argv=None):
    ytdl_common.sanitize_filename = ytdl_YoutubeDL.sanitize_filename = limit_len_sanitize_filename
    ytdl_common.InfoExtractor = NewInfoExtractor
    youtube_dl.extractor.GenericIE = GenericInfoExtractor
    youtube_dl.extractor.IwaraIE = IwaraIE
    youtube_dl.extractor.PornHubIE = PornHubIE
    youtube_dl.extractor.XVideosIE = XVideosIE
    youtube_dl.main(argv)
