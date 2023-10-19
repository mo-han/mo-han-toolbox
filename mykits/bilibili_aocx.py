#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bilibili mobile client APP offline cache extractor.
\"offline cache\" means downloaded content."""

import os
from glob import glob
import argparse

from mylib.sites.bilibili.__to_be_deprecated__ import BilibiliAppCacheEntry
from oldezpykit.stdlib.argparse import CompactHelpFormatterWithDefaults


def parse_args():
    common_parser_kwargs = {'formatter_class': CompactHelpFormatterWithDefaults}
    ap = argparse.ArgumentParser(**common_parser_kwargs,
                                 description='bilibili APP offline cache extractor')
    ap.add_argument('-c', '--cookies', help='netscape format cookies (text) file', metavar='<cookies_file>')
    ap.add_argument('folder', metavar='<folder>',
                    help='a bilibili app offline cache entry folder, usually named in digits, wildcard glob supported')
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
