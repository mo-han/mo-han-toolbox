#!/usr/bin/env python

import sys
import logging

from __dump__.hentai import HentaiCafeKit
from mylib.easy.logging import LOG_FMT_MESSAGE_ONLY
from mylib.easy.ostk import ensure_sigint_signal

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FMT_MESSAGE_ONLY
)


if __name__ == '__main__':
    ensure_sigint_signal()
    uri = sys.argv[1]
    if len(sys.argv) >= 3:
        hc = HentaiCafeKit(int(sys.argv[2]))
    else:
        hc = HentaiCafeKit(5)
    hc.save_entry_to_cbz(uri)
