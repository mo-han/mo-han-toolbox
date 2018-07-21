#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

from dota2_lib import Dota2Controller
from os.path import realpath, dirname
from sys import argv

__author__ = '墨焓 <zmhungrown@gmail.com>'
__program__ = 'dota2 waiter'
__version__ = 'demo'

if __name__ == '__main__':
    feed = dirname(realpath(argv[0])) + '/data/dota2_waiter'
    print('素材文件夹路径', realpath(feed))
    g = Dota2Controller(feed)
    g.auto_waiter((5, 20))
    