#!/usr/bin/env python3
# encoding=utf8
import os
import re
import subprocess
import hashlib
import filetype

from .os_util import pushd_context, read_json_file, write_json_file
from .tricks import get_logger, AttrTree, hex_hash

from typing import Iterable


def cmd_header(banner: bool = True, loglevel: str = None):
    cmd = ['ffmpeg']
    if not banner:
        cmd.append('-hide_banner')
    if loglevel:
        cmd.extend(['-loglevel', loglevel])
    return cmd


def cmd_append(cmd, *args, **kwargs):
    for a in args:
        cmd.append(str(a))
    for k, v in kwargs.items():
        cmd.extend(['-' + k, str(v)])


def concat(input_paths: Iterable[str], output_path: str,
           *output_opts,
           metadata_file_path: str = None,
           copy: bool = True, map_all_streams: bool = True,
           banner: bool = False, loglevel: str = 'warning',
           **output_kwargs):
    concat_list = '\n'.join(['file \'{}\''.format(e) for e in input_paths])
    cmd = cmd_header(banner, loglevel)
    cmd_append(cmd, f='concat', safe=0, protocol_whitelist='file,pipe', i='-')
    if metadata_file_path:
        cmd_append(cmd, i=metadata_file_path, map_metadata=1)
    if map_all_streams:
        cmd_append(cmd, map=0)
    if copy:
        cmd_append(cmd, c='copy')
    cmd_append(cmd, *output_opts, **output_kwargs)
    cmd.append(output_path)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    p.communicate(concat_list.encode())


def segment(input_path: str, output_path: str = None,
            *output_opts,
            copy: bool = True, map_all_streams: bool = True,
            banner: bool = False, loglevel: str = 'warning',
            **output_kwargs):
    if not output_path:
        _, ext = os.path.splitext(input_path)
        output_path = '%d.' + ext
    cmd = cmd_header(banner, loglevel)
    cmd_append(cmd, i=input_path, f='segment')
    if map_all_streams:
        cmd_append(cmd, map=0)
    if copy:
        cmd_append(cmd, c='copy')
    cmd_append(cmd, *output_opts, **output_kwargs)
    cmd.append(output_path)
    subprocess.run(cmd)


class AVSegmentsContainer:
    nickname = 'avsegcon'
    logger = get_logger(nickname)
    tag_filename = 'AV_SEGMENTS_CONTAINER.TAG'
    tag_signature = 'Signature: ' + hex_hash(tag_filename.encode())
    data_filename = 'data.json'
    param_filename = 'param.txt'
    source_segments_folder = 'i'

    class PathError(Exception):
        pass

    def __init__(self, path: str, work_dir: str = None):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise self.PathError("path not exist: '{}'".format(path))
        if os.path.isfile(path):
            input_path = path
            if filetype.guess(path).mime.startswith('video'):
                d, b = os.path.split(path)
                root_base = '.{}-{}-{}'.format(self.nickname, re.sub(r'\W+', '_', b), hex_hash(b.encode())[:8])
                work_dir = work_dir or d
                path = self.root = os.path.join(work_dir, root_base)
                if not os.path.isdir(path):
                    try:
                        os.makedirs(path, exist_ok=True)
                    except FileExistsError:
                        raise self.PathError("invalid container path used by file: '{}'".format(path))
                    self.write_tag_file()
                    with pushd_context(path):
                        os.makedirs(self.source_segments_folder)
                        with pushd_context(self.source_segments_folder):
                            segment(input_path)
            else:
                raise self.PathError("non-video file: '{}'".format(path))


    def write_tag_file(self):
        with pushd_context(self.root):
            with open(self.tag_filename, 'w') as f:
                f.write(self.tag_signature)

    def read_tag_file(self) -> str or None:
        with pushd_context(self.root):
            try:
                with open(self.tag_filename) as f:
                    return f.readline().rstrip('\r\n')
            except FileNotFoundError:
                return None

    def write_data_file(self):
        with pushd_context(self.root):
            write_json_file(self.data_filename, self.data.__data__, indent=0)

    def read_data_file(self) -> dict or None:
        with pushd_context(self.root):
            return read_json_file(self.data_filename) or None

    @property
    def data(self):
        return self.__data
