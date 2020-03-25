#!/usr/bin/env python3
# encoding=utf8
"""Windows OS only, need self-using batch script: you-get.bilibili.bat, ytdl.bat, etc."""

import re
import subprocess
import os


def get_cmd_result(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout, r.stderr


def get_video(url):
    o, _ = get_cmd_result('you-get.bilibili.bat download {}'.format(url))
    return o.decode().rsplit('\r\n\r\n', 2)[-2].rsplit('.cmt.xml ...', 1)[-2].split('Downloading ', 1)[1]


def split_part_title(s):
    part_title = re.sub(r'.+ \((P\d+\. .*)+\)', r'\1', s)
    return part_title


def get_filename(url):
    o, _ = get_cmd_result('ytdl.bat n {}'.format(url))
    return o.decode('ansi').rsplit('.', 1)[-2]


def rename(old, new):
    _, part_title = split_title(old)

    pass
