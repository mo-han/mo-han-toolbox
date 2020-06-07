#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bilibili (mobile client) application (offline cache) download extractor."""

import os
from glob import glob
import argparse

from mylib.bilibili import BilibiliAppCacheEntry
from mylib.struct import ArgumentParserCompactOptionHelpFormatter


def parse_args():
    common_parser_kwargs = {'formatter_class': ArgumentParserCompactOptionHelpFormatter}
    ap = argparse.ArgumentParser(**common_parser_kwargs)
    ap.add_argument('-c', '--cookies', help='netscape format cookies (text) file', metavar='cookies_file')
    ap.add_argument('folder', help='which is a bilibili app offline cache entry')
    return ap.parse_args()


def main():
    args = parse_args()
    cookies = args.cookies
    folders = glob(args.folder)
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        b = BilibiliAppCacheEntry(folder, cookies)
        b.extract_part()


if __name__ == '__main__':
    main()
