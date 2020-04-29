#!/usr/bin/env python

import sys
import logging

from lib_basic import LOG_FMT_MESSAGE_ONLY, win32_ctrl_c, ExitCode
from lib_hentai import NHentaiKit

if __name__ == '__main__':
    win32_ctrl_c()
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FMT_MESSAGE_ONLY,
    )
    nhk = NHentaiKit()
    try:
        nhk.save_gallery_to_cbz(nhk.get_gallery(sys.argv[1]))
    except KeyboardInterrupt:
        exit(ExitCode.CTRL_C)
