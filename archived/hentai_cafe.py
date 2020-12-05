#!/usr/bin/env python

import sys
import logging

from archived.hentai import HentaiCafeKit
from mylib.log import LOG_FMT_MESSAGE_ONLY
from mylib.os_lite import ensure_sigint_signal

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
