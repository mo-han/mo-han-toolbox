#!/usr/bin/env python3
# encoding=utf8
"""Windows OS only, need self-using batch script: bilidl.cmd , ytdl.cmd , etc."""

import re
import subprocess
import sys

from lib_base import win32_ctrl_c


def get_cmd_result(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE)
    return r.stdout


def get_video(url):
    o = get_cmd_result('bilidl.cmd download {}'.format(url)).decode()
    if '.cmt.xml ...' in o:
        o = o.rsplit('.cmt.xml ...\r\n', 1)[0]
        o = o.rsplit('\r\nDownloading ', 1)[-1]
    elif '.mp4 ...' in o:
        o = o.rsplit('.mp4 ...\r\n', 1)[0]
        o = o.rsplit('\r\nMerging video parts... Merged into', 1)[-1]
        o = o.rsplit('\r\nDownloading', 1)[-1]
    return o


def split_part_title(s):
    try:
        part_title = re.match(r'^(.+) \((P\d+\. .*)+\)$', s).group(2)
    except AttributeError:
        part_title = ''
    return part_title


def get_formatted_filename(url):
    o = get_cmd_result('ytdl.cmd n {}'.format(url)).decode('ansi')
    n = o.strip().rsplit('\n', 1)[-1].rsplit('.', 1)[-2]
    if n.startswith('活动作品'):
        n = n.split('活动作品', 1)[1]
    return n


def rename(old, new):
    pt = split_part_title(old)
    new_filename = ' '.join((new, pt)) if pt else new
    try:
        r = subprocess.run('bilidl.cmd rename "{}" "{}"'.format(old, new_filename))
        r.check_returncode()
    except FileNotFoundError:
        exit(1)
    except subprocess.CalledProcessError as e:
        print(e)
        exit(1)


def download(url):
    f = get_formatted_filename(url)
    v = get_video(url)
    rename(v, f)


if __name__ == '__main__':
    # win32_ctrl_c()
    download(sys.argv[1])
