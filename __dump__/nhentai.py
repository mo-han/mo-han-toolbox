#!/usr/bin/env python

import sys
import logging

from mylib._misc import ExitCode
from mylib.easy.logging import LOG_FMT_MESSAGE_ONLY
from mylib.easy.ostk import ensure_sigint_signal
from __dump__.hentai import NHentaiKit

if __name__ == '__main__':
    ensure_sigint_signal()
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FMT_MESSAGE_ONLY,
    )
    nhk = NHentaiKit()
    try:
        nhk.save_gallery_to_cbz(nhk.get_gallery(sys.argv[1]))
    except KeyboardInterrupt:
        exit(ExitCode.CTRL_C)
