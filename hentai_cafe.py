#!/usr/bin/env python

import sys
import zipfile
import requests
import logging

from lib_hentai import HentaiCafeKit, HentaiDownloadError
from lib_misc import LOG_FMT_MESSAGE_ONLY, win32_ctrl_c

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FMT_MESSAGE_ONLY
)


if __name__ == '__main__':
    win32_ctrl_c()
    uri = sys.argv[1]
    if len(sys.argv) >= 3:
        hc = HentaiCafeKit(int(sys.argv[2]))
    else:
        hc = HentaiCafeKit(5)
    hc.save_entry_to_cbz(uri)
