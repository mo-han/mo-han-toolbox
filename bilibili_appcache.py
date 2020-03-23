#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from glob import glob

from lib_bilibili import BilibiliAppCacheEntry
from lib_web import new_phantomjs

if __name__ == '__main__':
    # _, base = os.path.split(sys.argv[1])
    if sys.argv[1][-1] == '*':
        args = glob(sys.argv[1])
    else:
        args = sys.argv[1:]
    pj = new_phantomjs()
    for folder in args:
        if not os.path.isdir(folder):
            continue
        f = BilibiliAppCacheEntry(pj, folder)
        f.extract_part()
