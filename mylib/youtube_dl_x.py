#!/usr/bin/env python3
# encoding=utf8
from abc import ABCMeta
from importlib import import_module

import youtube_dl
from youtube_dl.extractor import common as ytdl_common
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import sanitize_filename

from . import fs
from .site_iwara import IwaraIE
from .site_pornhub import PornHubIE

# assert ytdl_common
# import module `youtube_dl.YoutubeDL` (forestalled by same name class `youtube_dl.YoutubeDL`)
ytdl_YoutubeDL = import_module('youtube_dl.YoutubeDL')


def limit_len_sanitize_filename(s, restricted=False, is_id=False):
    if not is_id:
        s = fs.sanitize_pu_200(s)
    return sanitize_filename(s, restricted=restricted, is_id=is_id)


def safe_title(extracted_data: dict):
    title = extracted_data['title']
    extracted_data['title'] = fs.sanitize_pu_200(title)


class NewInfoExtractor(InfoExtractor, metaclass=ABCMeta):
    """SEEMS LIKE NO EFFECT"""

    def extract(self, url):
        data = super().extract(url)
        safe_title(data)
        print(self.__class__.__name__, data['title'])


def youtube_dl_main_x(argv=None):
    ytdl_common.sanitize_filename = ytdl_YoutubeDL.sanitize_filename = limit_len_sanitize_filename
    ytdl_common.InfoExtractor = NewInfoExtractor
    youtube_dl.extractor.IwaraIE = IwaraIE
    youtube_dl.extractor.PornHubIE = PornHubIE
    youtube_dl.main(argv)
