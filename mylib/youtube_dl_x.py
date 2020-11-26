#!/usr/bin/env python3
# encoding=utf8
from importlib import import_module

import youtube_dl
from youtube_dl.extractor import common as ytdl_common
from youtube_dl.utils import sanitize_filename

from .fs import safe_name
from .text import ellipt_end
from .site_iwara import IwaraIE
from .site_pornhub import PornHubIE

# import module `youtube_dl.YoutubeDL` (forestalled by same name class `youtube_dl.YoutubeDL`)
ytdl_YoutubeDL = import_module('youtube_dl.YoutubeDL')


def safe_filename(s, restricted=False, is_id=False):
    print('before:', s)
    if not is_id:
        s = ellipt_end(safe_name(s), 210)
        print('after:', s)
    return sanitize_filename(s, restricted=restricted, is_id=is_id)


def youtube_dl_main_x(argv=None):
    ytdl_common.sanitize_filename = ytdl_YoutubeDL.sanitize_filename = safe_filename
    youtube_dl.extractor.IwaraIE = IwaraIE
    youtube_dl.extractor.PornHubIE = PornHubIE
    youtube_dl.main(argv)
