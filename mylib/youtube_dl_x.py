#!/usr/bin/env python3
# encoding=utf8
from importlib import import_module

import youtube_dl.extractor.common as ytdl_ex_common
import youtube_dl.utils

from .fs import safe_name
from .site_iwara import IwaraIE
from .site_pornhub import PornHubIE


def safe_filename(s, restricted=False, is_id=False):
    print(f'before safe: {s}')
    s = safe_name(s)
    print(f'after safe: {s}')
    return youtube_dl.utils.sanitize_filename(s, restricted=restricted, is_id=is_id)


ytdl_YoutubeDL = import_module('youtube_dl.YoutubeDL')
ytdl_YoutubeDL.sanitize_filename = safe_filename
youtube_dl.YoutubeDL = ytdl_YoutubeDL.YoutubeDL
ytdl_ex_common.sanitize_filename = safe_filename


def youtube_dl_main_x(argv=None):
    youtube_dl.extractor.IwaraIE = IwaraIE
    youtube_dl.extractor.PornHubIE = PornHubIE
    youtube_dl.utils.sanitize_filename = safe_filename
    youtube_dl.main(argv)
