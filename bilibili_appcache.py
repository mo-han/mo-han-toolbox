#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from glob import glob

from lib_bilibili import AppOfflineCacheFolder

if __name__ == '__main__':
    # _, base = os.path.split(sys.argv[1])
    if sys.argv[1][-1] == '*':
        args = glob(sys.argv[1])
    else:
        args = sys.argv[1:]
    for folder in args:
        if not os.path.isdir(folder):
            continue
        f = AppOfflineCacheFolder(folder)
        f.handle_part()
