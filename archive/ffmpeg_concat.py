#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from mylib.lamb_av_util import _concat_videos_deprecated

args = sys.argv[1:]
if args:
    _concat_videos_deprecated(*args)
else:
    print('{} input1 input2 ... output'.format(sys.argv[1]))
