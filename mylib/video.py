#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Some FFmpeg commands"""

import os
import ffmpeg

VIDEO_FILE_EXTENSIONS = ['.mp4', '.m4v', '.mkv', '.flv', '.webm']


class SegmentTranscode:
    pass


def choose_between_origin_and_hevc8b(file_path: str):
    if not os.path.isfile(file_path):
        print('# file not exist:', file_path)
        return
    tag_o = '__origin__'
    tag_h = 'hevc8b'
    another_tag_d = {tag_o: tag_h, tag_h: tag_o}
    sizes = {}
    files = {}
    folder, file = os.path.split(file_path)
    fname, ext = os.path.splitext(file)
    if ext not in VIDEO_FILE_EXTENSIONS:
        print('# is not video:', file_path)
        return
    try:
        fname, tag = fname.rsplit('.', maxsplit=1)
    except ValueError:
        print('# skip untagged video:', file_path)
        return
    try:
        another_tag_d = another_tag_d[tag]
    except ValueError:
        print('# skip untagged video:', file_path)
        return
    another_file = fname + '.' + another_tag_d + ext
    another_file_path = os.path.join(folder, another_file)
    if os.path.isfile(another_file_path):
        sizes[tag] = os.path.getsize(file_path)
        sizes[another_tag_d] = os.path.getsize(another_file_path)
        files[tag] = file_path
        files[another_tag_d] = another_file_path
        ratio = sizes[tag_h] / sizes[tag_o]
        diff = sizes[tag_o] - sizes[tag_h]
        if ratio <= 0.66 or ratio <= 0.75 and diff >= 50000000:
            file = files[tag_o]
            print('* remove large origin:', file)
            os.remove(file)
        else:
            file = files[tag_h]
            print('* remove large hevc8b:', file)
            os.remove(files[tag_h])
    else:
        print('# skip single video:', file_path)


def images_to_video(images_folder: str, output_video: str = None):
    pass


def _concat_videos_deprecated(*args):
    """concat_videos(part1, part2, part3, ... , output)"""
    input_list = args[:-1]
    output_path = args[-1]
    work_dir, _ = os.path.split(os.path.realpath(output_path))
    list_path = os.path.join(work_dir, '###-ffmpeg-concat-list-temp.txt')
    with open(list_path, 'w+b') as lf:
        for i in input_list:
            lf.write("file '{}'{}".format(i, os.linesep).encode())
    os.system(
        'ffmpeg -n -hide_banner -loglevel +level -f concat -safe 0 -i "{}" -c copy "{}"'
            .format(list_path, output_path))
    os.remove(list_path)


def concat_videos(input_list: list, output_path: str):
    work_dir, _ = os.path.split(os.path.realpath(output_path))
    list_path = os.path.join(work_dir, '###-ffmpeg-concat-list-temp.txt')
    with open(list_path, 'w+b') as lf:
        for i in sorted(input_list):
            lf.write("file '{}'{}".format(i, os.linesep).encode())
    os.system(
        # 'ffmpeg -n -hide_banner -loglevel +level -f concat -safe 0 -i "{}" -c copy "{}"'
        'ffmpeg -n -hide_banner -loglevel warning -f concat -safe 0 -i "{}" -c copy "{}"'
            .format(list_path, output_path))
    os.remove(list_path)


def merge_m4s(m4s_list: list, output_path: str):
    cmd = 'ffmpeg -n -hide_banner -loglevel warning '
    for m in m4s_list:
        cmd += '-i "{}" '.format(m)
    cmd += '-codec copy "{}"'.format(output_path)
    os.system(cmd)
