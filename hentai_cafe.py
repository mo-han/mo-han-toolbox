#!/usr/bin/env python

import sys
import zipfile
import requests
import logging

from lib_hentai import HentaiCafeKit
from lib_misc import LOG_FMT_MESSAGE_ONLY

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FMT_MESSAGE_ONLY
)
hc = HentaiCafeKit(10)


if __name__ == '__main__':
    uri = sys.argv[1]
    hc.save_entry_to_cbz(uri)
    if hc.alert:
        exit(1)
    else:
        exit()
