#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Some FFmpeg commands"""

import os


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
    cmd = 'ffmpeg '
    for m in m4s_list:
        cmd += '-i "{}" '.format(m)
    cmd += '-codec copy "{}"'.format(output_path)
    os.system(cmd)
