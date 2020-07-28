#!/usr/bin/env python3
# encoding=utf8
import os
import re
import subprocess
from typing import Iterable

import ffmpeg
import filetype

from .os_util import pushd_context, write_json_file, read_json_file, SliceFileIO
from .tricks import get_logger, hex_hash, argv_choices


class UsefulCommand:
    exe = 'ffmpeg'
    head = [exe]
    body = []

    def __init__(self, banner: bool = True, loglevel: str = None, overwrite: bool = None):
        self.set_head(banner=banner, loglevel=loglevel, overwrite=overwrite)

    @property
    def cmd(self):
        return self.head + self.body

    def set_head(self, banner: bool = True, loglevel: str = None, overwrite: bool = None, verbose: str = None):
        h = [self.exe]
        if not banner:
            h.append('-hide_banner')
        if loglevel:
            h.extend(['-loglevel', loglevel])
        if overwrite is True:
            h.append('-y')
        elif overwrite is False:
            h.append('-n')
        if verbose:
            h.extend(['-v', verbose])
        self.head = h

    def set_args(self, *args, **kwargs):
        for a in args:
            self.body.append(str(a))
        for k, v in kwargs.items():
            self.body.extend(['-' + k, str(v)])

    def del_args(self):
        self.body = []

    def proc_comm(self, input_bytes: bytes):
        cmd = self.head + self.body
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        p.communicate(input_bytes)

    def proc_run(self):
        cmd = self.head + self.body
        subprocess.run(cmd)

    @argv_choices({'map_preset': ('all', 'video-only', 'audio-only', None)})
    def concat(self, input_paths: Iterable[str], output_path: str,
               *output_opts,
               metadata_file_path: str = None,
               copy: bool = True, map_preset: str = None,
               **output_kwargs):
        self.del_args()
        concat_list = '\n'.join(['file \'{}\''.format(e) for e in input_paths])
        self.set_args(f='concat', safe=0, protocol_whitelist='file,pipe', i='-')
        if metadata_file_path:
            self.set_args(i=metadata_file_path, map_metadata=1)
        if map_preset == 'all':
            self.set_args(map=0)
        elif map_preset == 'video-only':
            self.set_args(map='0:V')
        elif map_preset == 'audio-only':
            self.set_args(map='0:a')
        if copy:
            self.set_args(c='copy')
        self.set_args(*output_opts, **output_kwargs)
        self.set_args(output_path)
        self.proc_comm(concat_list.encode())

    @argv_choices({'map_preset': ('all', 'video-only', 'audio-only', None)})
    def segment(self, input_path: str, output_path: str = None,
                *output_opts,
                copy: bool = True, map_preset: str = None,
                **output_kwargs):
        self.del_args()
        if not output_path:
            output_path = '%d' + os.path.splitext(input_path)[-1]
        self.set_args(i=input_path, f='segment')
        if map_preset == 'all':
            self.set_args(map=0)
        elif map_preset == 'video-only':
            self.set_args(map='0:V')
        elif map_preset == 'audio-only':
            self.set_args(map='0:a')
        if copy:
            self.set_args(c='copy')
        self.set_args(*output_opts, **output_kwargs)
        self.set_args(output_path)
        self.proc_run()

    def metadata_file(self, input_path: str, output_path: str):
        self.del_args()
        self.set_args(i=input_path, f='ffmetadata')
        self.set_args(output_path)
        self.proc_run()


class VideoSegmentsContainer:
    nickname = 'vsgcon'
    logger = get_logger(nickname)
    cmd = UsefulCommand(banner=False, loglevel='warning')
    tag_file = 'VIDEO_SEGMENTS_CONTAINER.TAG'
    tag_sig = 'Signature: ' + hex_hash(tag_file.encode())
    param_file = 'param.txt'
    metadata_file = 'metadata.txt'
    filename_file_fmt = 'filename={}.txt'
    input_stream_prefix = 'i'
    input_json = 'input.json'
    input_path = None
    input_data = None

    class PathError(Exception):
        pass

    class ContainerError(Exception):
        pass

    def __init__(self, path: str, work_dir: str = None):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise self.PathError("path not exist: '{}'".format(path))
        if os.path.isfile(path):
            self.input_path = path
            if filetype.guess(path).mime.startswith('video'):
                d, b = os.path.split(path)
                self.input_data = {'source_filename': b}
                with SliceFileIO(path) as fl:
                    fl_middle = len(fl) // 2
                    root_base = '.{}-{}'.format(
                        self.nickname,
                        hex_hash(fl[:4096] + fl[fl_middle - 2048:fl_middle + 2048] + fl[:-4096])[:7],
                    )
                work_dir = work_dir or d
                path = self.root = os.path.join(work_dir, root_base)
                if not os.path.isdir(path):
                    try:
                        os.makedirs(path, exist_ok=True)
                    except FileExistsError:
                        raise self.PathError("invalid folder path used by file: '{}'".format(path))
                    self.tag()
                    self.segment()
            else:
                raise self.PathError("non-video file: '{}'".format(path))
        if os.path.isdir(path):
            self.root = path
            if not self.has_tag():
                raise self.ContainerError("non-container folder: '{}'".format(path))
            if not self.has_segments():
                self.segment()
            self.read_input_json()

    def segment(self):
        if not self.input_path:
            raise self.PathError('no source file path')
        with pushd_context(self.root):
            os.makedirs(self.input_stream_prefix)
            with pushd_context(self.input_stream_prefix):
                self.cmd.segment(self.input_path, map_preset='video-only')
            self.write_metadata()
            self.write_input_json()

    def write_metadata(self):
        with pushd_context(self.root):
            self.cmd.metadata_file(self.input_path, self.metadata_file)
            with open(self.metadata_file) as f:
                meta_lines = f.readlines()
            meta_lines = [line for line in meta_lines if line.split('=', maxsplit=1)[0] not in
                          ('encoder', 'major_brand', 'minor_version', 'compatible_brands')]
            with open(self.metadata_file, 'w') as f:
                f.writelines(meta_lines)

    def tag(self):
        with pushd_context(self.root):
            with open(self.tag_file, 'w') as f:
                f.write(self.tag_sig)

    def write_input_json(self):
        d = self.input_data or {}
        d['source_segments'] = {}
        with pushd_context(self.root):
            with pushd_context(self.input_stream_prefix):
                for f in os.listdir('.'):
                    few = {}
                    many = ffmpeg.probe(f)
                    for s in many['streams']:
                        if s['codec_type'] == 'video' and s['disposition']['default']:
                            try:
                                few['bit_rate'] = s['bit_rate']
                            except KeyError:
                                few['bit_rate'] = many['format']['bit_rate']
                            few['codec_name'] = s['codec_name']
                            few['height'] = s['height']
                            few['width'] = s['width']
                            few['pix_fmt'] = s['pix_fmt']
                            break
                    d['source_segments'][f] = few
            write_json_file(self.input_json, d, indent=4)
            self.input_data = d

    def read_input_json(self):
        with pushd_context(self.root):
            self.input_data = read_json_file(self.input_json)

    def has_tag(self) -> bool:
        with pushd_context(self.root):
            try:
                with open(self.tag_file) as f:
                    return f.readline().rstrip('\r\n') == self.tag_sig
            except FileNotFoundError:
                return False

    def has_segments(self) -> bool:
        self.read_input_json()
        return bool(self.input_data)
