#!/usr/bin/env python3
# encoding=utf8
import os
import re
import subprocess
from typing import Iterable

import filetype
import ffmpeg

from .os_util import pushd_context, write_json_file, read_json_file
from .tricks import get_logger, hex_hash


class UsefulCommand:
    exe = 'ffmpeg'
    head = [exe]
    body = []

    def __init__(self, banner: bool = True, loglevel: str = None, overwrite: bool = None):
        self.set_head(banner=banner, loglevel=loglevel, overwrite=overwrite)

    def set_head(self, banner: bool = True, loglevel: str = None, overwrite: bool = None):
        h = [self.exe]
        if not banner:
            h.append('-hide_banner')
        if loglevel:
            h.extend(['-loglevel', loglevel])
        if overwrite is True:
            h.append('-y')
        elif overwrite is False:
            h.append('-n')
        self.head = h

    def set_args(self, *args, **kwargs):
        body = []
        for a in args:
            body.append(str(a))
        for k, v in kwargs.items():
            body.extend(['-' + k, str(v)])
        self.body = body

    def proc_comm(self, input_bytes: bytes):
        cmd = self.head + self.body
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        p.communicate(input_bytes)

    def proc_run(self):
        cmd = self.head + self.body
        subprocess.run(cmd)

    def concat(self, input_paths: Iterable[str], output_path: str,
               *output_opts,
               metadata_file_path: str = None,
               copy: bool = True, map_all_streams: bool = True,
               **output_kwargs):
        concat_list = '\n'.join(['file \'{}\''.format(e) for e in input_paths])
        self.set_args(f='concat', safe=0, protocol_whitelist='file,pipe', i='-')
        if metadata_file_path:
            self.set_args(i=metadata_file_path, map_metadata=1)
        if map_all_streams:
            self.set_args(map=0)
        if copy:
            self.set_args(c='copy')
        self.set_args(*output_opts, **output_kwargs)
        self.set_args(output_path)
        self.proc_comm(concat_list.encode())

    def segment(self, input_path: str, output_path: str = None,
                *output_opts,
                copy: bool = True, map_all_streams: bool = True,
                **output_kwargs):
        if not output_path:
            output_path = '%d' + os.path.splitext(input_path)[-1]
        self.set_args(i=input_path, f='segment')
        if map_all_streams:
            self.set_args(map=0)
        if copy:
            self.set_args(c='copy')
        self.set_args(*output_opts, **output_kwargs)
        self.set_args(output_path)
        self.proc_run()

    def metadata_file(self, input_path: str, output_path: str):
        self.set_args(i=input_path, f='ffmetadata')
        self.set_args(output_path)
        self.proc_run()


class VideoSegmentsContainer:
    nickname = 'vsgcon'
    logger = get_logger(nickname)
    cmd = UsefulCommand(banner=False, loglevel='warning')
    tag_file = 'VIDEO_SEGMENTS_CONTAINER.TAG'
    tag_sig = 'Signature: ' + hex_hash(tag_file.encode())
    data_file = 'data.json'
    param_file = 'param.txt'
    metadata_file = 'metadata.txt'
    source_segments_folder = 'source'
    source_path = None
    data = None

    class PathError(Exception):
        pass

    class ContainerError(Exception):
        pass

    def __init__(self, path: str, work_dir: str = None):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise self.PathError("path not exist: '{}'".format(path))
        if os.path.isfile(path):
            self.source_path = path
            if filetype.guess(path).mime.startswith('video'):
                d, b = os.path.split(path)
                root_base = '.{}-{}-{}'.format(self.nickname, re.sub(r'\W+', '_', b).strip('_'),
                                               hex_hash(b.encode())[:8])
                work_dir = work_dir or d
                path = self.root = os.path.join(work_dir, root_base)
                if not os.path.isdir(path):
                    try:
                        os.makedirs(path, exist_ok=True)
                    except FileExistsError:
                        raise self.PathError("invalid folder path used by file: '{}'".format(path))
                    self.tag()
                    self.segment_source()
            else:
                raise self.PathError("non-video file: '{}'".format(path))
        if os.path.isdir(path):
            self.root = path
            if not self.has_tag():
                raise self.ContainerError("non-container folder: '{}'".format(path))
            if not self.has_segments():
                self.segment_source()
            self.read_data()

    def segment_source(self):
        if not self.source_path:
            raise self.PathError('no source file path')
        with pushd_context(self.root):
            os.makedirs(self.source_segments_folder)
            with pushd_context(self.source_segments_folder):
                self.cmd.segment(self.source_path)
            self.cmd.metadata_file(self.source_path, self.metadata_file)
            self.write_data()

    def tag(self):
        with pushd_context(self.root):
            with open(self.tag_file, 'w') as f:
                f.write(self.tag_sig)

    def write_data(self):
        d = {'source': {}}
        with pushd_context(self.root):
            with pushd_context(self.source_segments_folder):
                for f in os.listdir('.'):
                    few = {}
                    many = ffmpeg.probe(f)
                    for s in many['streams']:
                        if s['codec_type'] == 'video' and s['disposition']['default']:
                            few['video_bit_rate'] = s['bit_rate']
                            few['video_codec_name'] = s['codec_name']
                            few['video_height'] = s['height']
                            few['video_width'] = s['width']
                            few['video_pix_fmt'] = s['pix_fmt']
                            break
                    d['source'][f] = few
            write_json_file(self.data_file, d, indent=0)
            self.data = d

    def read_data(self):
        with pushd_context(self.root):
            self.data = read_json_file(self.data_file)

    def has_tag(self) -> bool:
        with pushd_context(self.root):
            try:
                with open(self.tag_file) as f:
                    return f.readline().rstrip('\r\n') == self.tag_sig
            except FileNotFoundError:
                return False

    def has_segments(self) -> bool:
        self.read_data()
        return bool(self.data)
