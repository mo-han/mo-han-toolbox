#!/usr/bin/env python3
# encoding=utf8
import os
import subprocess

from typing import Iterable


def cmd_header(banner: bool = True, loglevel: str = None):
    cmd = ['ffmpeg']
    if not banner:
        cmd.append('-hide_banner')
    if loglevel:
        cmd.extend(['-loglevel', loglevel])
    return cmd


def cmd_extend(cmd, *args, **kwargs):
    for a in args:
        cmd.append(str(a))
    for k, v in kwargs.items():
        cmd.extend(['-' + k, str(v)])


def concat(input_paths: Iterable[str], output_path: str,
           *output_opts,
           metadata_file_path: str = None,
           banner: bool = False, loglevel: str = 'warning', copy: bool = True, map_all_streams: bool = True,
           **output_kwargs):
    concat_list = '\n'.join(['file \'{}\''.format(e) for e in input_paths])
    cmd = cmd_header(banner, loglevel)
    cmd_extend(cmd, f='concat', safe=0, protocol_whitelist='file,pipe', i='-')
    if metadata_file_path:
        cmd_extend(cmd, i=metadata_file_path, map_metadata=1)
    if map_all_streams:
        cmd_extend(cmd, map=0)
    if copy:
        cmd_extend(cmd, c='copy')
    cmd_extend(cmd, *output_opts, **output_kwargs)
    cmd.append(output_path)
    print(cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    p.communicate(concat_list.encode())


def segment(input_path: str, output_path: str,
            *output_opts,
            banner: bool = False, loglevel: str = 'warning', copy: bool = True, map_all_streams: bool = True,
            **output_kwargs):
    cmd = cmd_header(banner, loglevel)
    cmd_extend(cmd, i=input_path, f='segment')
    if map_all_streams:
        cmd_extend(cmd, map=0)
    if copy:
        cmd_extend(cmd, '-c', 'copy')
    cmd_extend(cmd, *output_opts, **output_kwargs)
    cmd.append(output_path)


class SegmentsContainer:
    def __init__(self, source_file_path: str, work_dir: str = None):
        d, b = os.path.split(source_file_path)
        self._work_dir = work_dir or d

    @property
    def work_dir(self):
        return self._work_dir
