#!/usr/bin/env python

import sys
import logging

from mylib.misc import ExitCode
from mylib.log import LOG_FMT_MESSAGE_ONLY
from mylib.os_util import ensure_sigint_signal
from archived.hentai import NHentaiKit

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
