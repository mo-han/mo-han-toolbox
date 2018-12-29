#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from lib_ffmpeg_wrap import concat_videos

args = sys.argv[1:]
if args:
    concat_videos(*args)
else:
    print('{} input1 input2 ... output'.format(sys.argv[1]))
