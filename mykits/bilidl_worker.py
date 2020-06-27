#!/usr/bin/env python3
# encoding=utf8
"""Windows OS only, need self-using batch script: bilidl.cmd , ytdl.cmd , etc."""

import argparse
import os
import re
import shutil
import subprocess

from mylib.misc import random_fname
from mylib.util import ensure_sigint_signal


def auto_complete_url(url: str):
    if '"' in url:
        url = url.strip('"')
    if url[:4] == 'http':
        return url
    if url[0] == '[' and url[-1] == ']':
        url = 'https://b23.tv/' + url[1:-1]
    if url[:2].lower() in ('bv', 'av'):
        url = 'https://b23.tv/' + url
    return url


def get_cmd_result(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE)
    return r.stdout


def filename_of_download_video(url):
    o = get_cmd_result('bilidl.cmd download {}'.format(url)).decode()
    if '.cmt.xml ...' in o:
        o = o.rsplit('.cmt.xml ...\r\n', 1)[0]
        o = o.rsplit('\r\nDownloading ', 1)[-1]
    elif '.mp4 ...' in o:
        o = o.rsplit('.mp4 ...\r\n', 1)[0]
        o = o.rsplit('\r\nMerging video parts... Merged into', 1)[-1]
        o = o.rsplit('\r\nDownloading', 1)[-1]
    return o


def split_part_name(filename):
    try:
        part_title = re.match(r'^(.+) \((P\d+\. .*)+\)$', filename).group(2)
        return part_title
    except AttributeError:
        return


def get_formatted_filename(url):
    try:
        o = get_cmd_result('ytdl.cmd n {}'.format(url)).decode()
    except UnicodeDecodeError:
        o = get_cmd_result('ytdl.cmd n {}'.format(url)).decode('ansi')
    fname = o.strip().rsplit('\n', 1)[-1].rsplit('.', 1)[-2]
    if fname.startswith('活动作品'):
        fname = fname.split('活动作品', 1)[1]
    return fname


def get_formatted_meta(formatted_filename: str):
    return re.sub(r'^.+ (\[(\w+)\]\[(.+)\])$', r'[\1][\2]', formatted_filename)


def __deprecated_rename(old, new):
    pt = split_part_name(old)
    new_filename = ' '.join((new, pt)) if pt else new
    try:
        r = subprocess.run('bilidl.cmd rename "{}" "{}"'.format(old, new_filename))
        r.check_returncode()
    except FileNotFoundError:
        exit(1)
    except subprocess.CalledProcessError as e:
        print(e)
        exit(1)


def __deprecated_download(url):
    f = get_formatted_filename(url)
    v = filename_of_download_video(url)
    __deprecated_rename(v, f)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='bilibili video url')
    parser.add_argument('options', nargs='?', help='you-get options')
    return parser.parse_known_args()


def main():
    args, unknown_args_l = parse_args()
    url = args.url
    opt = args.options
    if opt:
        unknown_args_l.append(opt)
    url = auto_complete_url(url)
    print(url)

    folder = random_fname(prefix='__bilidltemp', suffix='__')
    os.mkdir(folder)
    os.chdir(folder)
    dl_cmd = 'you-get {} {}'.format(' '.join(unknown_args_l), url)
    print(dl_cmd)
    os.system(dl_cmd)
    pretty_fname = get_formatted_filename(url)
    files = os.listdir(os.curdir)
    for f in files:
        if f[-8:].lower() == '.cmt.xml':
            fname, ext = f[:-8], '.xml'
        else:
            fname, ext = f[:-4], f[-4:]
        part = split_part_name(fname)
        new_f = '{}{}{}'.format(pretty_fname, ' ' + part if part else '', ext)
        os.rename(f, new_f)
        print('{} -> {}'.format(f, new_f))
        try:
            shutil.move(new_f, os.pardir)
        except shutil.Error:
            os.remove(os.path.join(os.pardir, new_f))
            shutil.move(new_f, os.pardir)
    os.chdir(os.pardir)
    os.removedirs(folder)
    # if ' -i ' in dl_cmd:
    #     print('PRESS ANY KEY TO CONTINUE')
    #     getch()


if __name__ == '__main__':
    ensure_sigint_signal()
    main()
