#!/usr/bin/env python3
# encoding=utf8
import youtube_dl.extractor

from mylib.website_iwara import IwaraIE
from mylib.website_ph import PornHubIE


def youtube_dl_main_x(argv=None):
    youtube_dl.extractor.IwaraIE = IwaraIE
    youtube_dl.extractor.PornHubIE = PornHubIE
    youtube_dl.main(argv)