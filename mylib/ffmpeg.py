#!/usr/bin/env python3
# encoding=utf8
import os
import re
import subprocess
import hashlib
import filetype

from .os_util import pushd_context, read_json_file
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


def segment(input_path: str, output_path: str,
            *output_opts,
            copy: bool = True, map_all_streams: bool = True,
            banner: bool = False, loglevel: str = 'warning',
            **output_kwargs):
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
    tag_filename = 'AV_SEGMENTS_CONTAINER.TAG'
    tag_signature = 'Signature: ' + hex_hash(tag_filename.encode())
    config_filename = 'config.json'
    
    _nickname = 'avsegcon'
    _cls_logger = get_logger(_nickname)

    def __init__(self, path: str, work_dir: str = None, logger=_cls_logger):
        if not os.path.exists(path):
            raise ValueError("path not exist: '{}'".format(path))
        if os.path.isfile(path):
            if filetype.guess(path).mime.startswith('video'):
                path = os.path.abspath(path)
                d, b = os.path.split(path)
                root_base = '.{}-{}-{}'.format(self._nickname, re.sub('\W+', '_', b), hex_hash(b.encode())[:8])
                work_dir = work_dir or d
                path = root = os.path.join(work_dir, root_base)
            else:
                raise ValueError("non-video file: '{}'".format(path))
        if os.path.isdir(path):
            with pushd_context(path):
                tag_file = self.tag_filename
                if os.path.isfile(tag_file):
                    with open(tag_file) as f:
                        sig = f.readline().rstrip('\r\n')
                    if sig == self.tag_signature:
                        j = read_json_file()

        self.__data = AttrTree()
        self.data.path = os.path.abspath(path)

    @property
    def data(self):
        return self.__data

    def write_source_hash(self):
        ...

    def chdir_root(self):
