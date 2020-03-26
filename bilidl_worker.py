#!/usr/bin/env python3
# encoding=utf8
"""Windows OS only, need self-using batch script: you-get.bilibili.bat, ytdl.bat, etc."""

import re
import subprocess
import sys

from lib_base import win32_ctrl_c


def get_cmd_result(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE)
    return r.stdout


def get_video(url):
    o = get_cmd_result('you-get.bilibili.bat download {}'.format(url))
    return o.decode().rsplit('.cmt.xml ...', 1)[-2].split('Downloading ', 1)[1]


def split_part_title(s):
    try:
        part_title = re.match(r'^(.+) \((P\d+\. .*)+\)$', s).group(2)
    except AttributeError:
        part_title = ''
    return part_title


def get_formatted_filename(url):
    o = get_cmd_result('ytdl.bat n {}'.format(url))
    return o.decode('ansi').rsplit('.', 1)[-2]


def rename(old, new):
    pt = split_part_title(old)
    new_filename = ' '.join((new, pt)) if pt else new
    try:
        subprocess.run('you-get.bilibili.bat rename "{}" "{}"'.format(old, new_filename))
    except FileNotFoundError:
        exit(1)


def download(url):
    v = get_video(url)
    rename(v, get_formatted_filename(url))


if __name__ == '__main__':
    # win32_ctrl_c()
    download(sys.argv[1])
