#!/usr/bin/env python3
# encoding=utf8
import os
import shlex
import shutil
import subprocess
from typing import Iterable

import ffmpeg
import filetype

from .os_util import pushd_context, write_json_file, read_json_file, SlicedFileIO, ensure_open_file
from .tricks import get_logger, hex_hash, decorator_factory_args_choices

TXT_FILENAME = 'filename'
TXT_ALL = 'all'
TXT_ONLY_VIDEO = 'only video'
TXT_ONLY_PICTURE = 'only picture'
TXT_ONLY_AUDIO = 'only audio'
TXT_ONLY_SUBTITLE = 'only subtitle'
TXT_ONLY_DATA = 'only data'
TXT_ONLY_ATTACHMENT = 'only attachment'
TXT_NO_VIDEO = 'no video'
TXT_NO_AUDIO = 'no audio'
TXT_NO_SUBTITLE = 'no subtitle'
TXT_NO_DATA = 'no data'
TXT_NO_ATTACHMENT = 'no attachment'
TXT_FIRST_VIDEO = 'first video'
STREAM_MAP_PRESET_TABLE = {TXT_ALL: ['0'], TXT_ONLY_VIDEO: ['0:V'], TXT_ONLY_AUDIO: ['0:a'],
                           TXT_ONLY_SUBTITLE: ['0:s'], TXT_ONLY_ATTACHMENT: ['0:t'], TXT_ONLY_DATA: ['0:d'],
                           TXT_NO_VIDEO: ['0', '-0:V'], TXT_NO_AUDIO: ['0', '-0:a'], TXT_NO_SUBTITLE: ['0', '-0:s'],
                           TXT_NO_ATTACHMENT: ['0', '-0:t'], TXT_NO_DATA: ['0', '-0:d'],
                           TXT_FIRST_VIDEO: ['0:V:0'], TXT_ONLY_PICTURE: ['0:v', '-0:V']}
CODEC_NAME_TO_FILEXT_TABLE = {'mjpeg': '.jpg', 'png': '.png', 'hevc': '.mp4', 'h264': '.mp4', 'vp9': '.webm'}

decorator_choose_map_preset = decorator_factory_args_choices({'map_preset': STREAM_MAP_PRESET_TABLE.keys()})


def filext_from_codec_name(x) -> str:
    d = CODEC_NAME_TO_FILEXT_TABLE
    if isinstance(x, str):
        return d[x]
    elif isinstance(x, dict) and 'codec_name' in x:
        return d[x['codec_name']]
    else:
        raise TypeError(x)


def excerpt_single_video_stream(filepath: str) -> dict:
    d = {}
    data = ffmpeg.probe(filepath)
    whole_file = data['format']
    streams = data['streams']
    if len(streams) == 1:
        single_stream = streams[0]
        if single_stream['codec_type'] == 'video' and single_stream['disposition']['attached_pic'] == 0:
            d['size'] = int(whole_file['size'])
            d['start_time'] = start_time = float(single_stream.get('start_time', whole_file['start_time']))
            duration = float(single_stream.get('duration', whole_file['duration']))
            d['duration'] = round((duration - start_time) * 1000000) / 1000000
            d['bit_rate'] = int(d['size'] // d['duration'])
            d['codec_name'] = single_stream['codec_name']
            d['height'] = single_stream['height']
            d['with'] = single_stream['width']
            d['pix_fmt'] = single_stream['pix_fmt']
    return d


class FFmpegCommandCaller:
    exe = 'ffmpeg'
    head = [exe]
    body = []
    to_pipe = False

    class FFmpegError(Exception):
        pass

    def __init__(self, banner: bool = True, loglevel: str = None, overwrite: bool = None, to_pipe: bool = False):
        self.to_pipe = to_pipe
        self.set_head(banner=banner, loglevel=loglevel, overwrite=overwrite)

    @property
    def cmd(self):
        return self.head + self.body

    def set_head(self, banner: bool = True, loglevel: str = None, verbose: str = None,
                 threads: int = None, overwrite: bool = None):
        h = [self.exe]
        if not banner:
            h.append('-hide_banner')
        if loglevel:
            h.extend(['-loglevel', loglevel])
        if verbose:
            h.extend(['-v', verbose])
        if overwrite is True:
            h.append('-y')
        elif overwrite is False:
            h.append('-n')
        if threads:
            h.extend(['-threads', str(threads)])
        self.head = h

    def set_args(self, *args, **kwargs):
        for a in args:
            self.body.append(str(a))
        for k, v in kwargs.items():
            if isinstance(v, str):
                maps = [v]
            elif isinstance(v, Iterable):
                maps = v
            else:
                return
            for m in maps:
                self.body.extend(['-' + k.replace('__', ':'), str(m)])

    def reset_args(self):
        self.body = []

    def set_map_preset(self, map_preset: str):
        if not map_preset:
            return
        for m in STREAM_MAP_PRESET_TABLE[map_preset]:
            self.set_args(map=m)

    def proc_comm(self, input_bytes: bytes) -> tuple:
        cmd = self.head + self.body
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        out, err = p.communicate(input_bytes)
        code = p.returncode
        if code:
            raise self.FFmpegError(code, (out or b'').decode(), (err or b'').decode())
        else:
            return (out or b'').decode(), (err or b'').decode()

    def proc_run(self) -> tuple:
        cmd = self.head + self.body
        # print(cmd)
        if self.to_pipe:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p = subprocess.run(cmd)
        code = p.returncode
        if code:
            raise self.FFmpegError(code, (p.stdout or b'').decode(), (p.stderr or b'').decode())
        else:
            return (p.stdout or b'').decode(), (p.stderr or b'').decode()

    @decorator_choose_map_preset
    def concat(self, input_paths: Iterable[str], output_path: str, extra_inputs: Iterable[str] = (), *output_opts,
               metadata_filepath: str = None, copy: bool = True, map_preset: str = None, **output_kwargs):
        self.reset_args()
        concat_list = '\n'.join(['file \'{}\''.format(e) for e in input_paths])
        self.set_args(f='concat', safe=0, protocol_whitelist='file,pipe', i='-')
        if extra_inputs:
            for file in extra_inputs:
                self.set_args(i=file)
        if metadata_filepath:
            self.set_args(i=metadata_filepath, map_metadata=1)
        if copy:
            self.set_args(c='copy')
            inputs_count = 1 + len(list(extra_inputs))
            for i in range(inputs_count):
                self.set_args(map=i)
        self.set_map_preset(map_preset)
        self.set_args(*output_opts, **output_kwargs)
        self.set_args(output_path)
        return self.proc_comm(concat_list.encode())

    @decorator_choose_map_preset
    def segment(self, input_path: str, output_path: str = None, *output_opts,
                copy: bool = True, map_preset: str = None, **output_kwargs):
        self.reset_args()
        if not output_path:
            output_path = '%d' + os.path.splitext(input_path)[-1]
        self.set_args(i=input_path, f='segment')
        if copy:
            self.set_args(c='copy')
        self.set_map_preset(map_preset)
        self.set_args(*output_opts, **output_kwargs)
        self.set_args(output_path)
        return self.proc_run()

    @decorator_choose_map_preset
    def extract(self, input_path: str, output_path: str, *output_opts,
                copy: bool = True, map_preset: str = None, **output_kwargs):
        self.reset_args()
        self.set_args(i=input_path)
        if copy:
            self.set_args(c='copy')
        self.set_map_preset(map_preset)
        self.set_args(*output_opts, **output_kwargs)
        self.set_args(output_path)
        return self.proc_run()

    def metadata_file(self, input_path: str, output_path: str):
        self.reset_args()
        self.set_args(i=input_path, f='ffmetadata')
        self.set_args(output_path)
        return self.proc_run()


class VideoSegmentsContainer:
    nickname = 'video_seg_con'
    logger = get_logger(nickname)
    cmd = FFmpegCommandCaller(banner=False, loglevel='warning', overwrite=True)
    tag_file = 'VIDEO_SEGMENTS_CONTAINER.TAG'
    tag_sig = 'Signature: ' + hex_hash(tag_file.encode())
    param_file = 'param.txt'
    metadata_file = 'metadata.txt'
    input_prefix = 'i'
    input_filename_fmt = input_prefix + '={}'
    input_picture = input_prefix + '-p.mp4'
    input_non_video = input_prefix + '-nv.mkv'
    input_json = input_prefix + '.json'
    input_filepath = None
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
            self.input_filepath = path
            if filetype.guess(path).mime.startswith('video'):
                d, b = os.path.split(path)
                self.input_data = {TXT_FILENAME: b}
                with SlicedFileIO(path) as f_cut:
                    fl_middle = len(f_cut) // 2
                    root_base = '.{}-{}'.format(self.nickname, hex_hash(
                        f_cut[:4096] + f_cut[fl_middle - 2048:fl_middle + 2048] + f_cut[:-4096])[:7])
                work_dir = work_dir or d
                path = self.root = os.path.join(work_dir, root_base)
                if not os.path.isdir(path):
                    try:
                        os.makedirs(path, exist_ok=True)
                    except FileExistsError:
                        raise self.PathError("invalid folder path used by file: '{}'".format(path))
                    self.tag()
                    self.split()
            else:
                raise self.PathError("non-video file: '{}'".format(path))

        if os.path.isdir(path):
            self.root = path
            if not self.has_tag():
                raise self.ContainerError("non-container folder: '{}'".format(path))
            if not self.has_segments():
                self.split()
            self.read_input_json()
            if TXT_FILENAME not in self.input_data:
                self.get_filename()

        self.set_filename()

    def set_filename(self):
        fn = self.input_data.get(TXT_FILENAME)
        if not fn:
            return
        with pushd_context(self.root):
            ensure_open_file(self.input_filename_fmt.format(fn))

    def get_filename(self):
        filename_prefix = self.input_filename_fmt.format('')
        with pushd_context(self.root):
            for f in os.listdir('.'):
                if f.startswith(filename_prefix) and os.path.isfile(f):
                    filename = f.lstrip(filename_prefix)
                    self.input_data[TXT_FILENAME] = filename
                    return filename
            else:
                raise self.ContainerError('no filename found')

    def split(self):
        file = self.input_filepath
        folder_prefix = self.input_prefix + '-'
        if not file:
            raise self.PathError('no source file path')

        with pushd_context(self.root):
            for stream in ffmpeg.probe(file, select_streams='V')['streams']:
                index = stream['index']
                codec = stream['codec_name']
                suitable_filext = CODEC_NAME_TO_FILEXT_TABLE.get(codec)
                if suitable_filext:
                    segment_output = '%d' + suitable_filext
                else:
                    segment_output = None
                seg_folder = folder_prefix + str(index)
                os.makedirs(seg_folder, exist_ok=True)
                with pushd_context(seg_folder):
                    self.cmd.segment(file, segment_output, map='0:{}'.format(index))
            try:
                self.cmd.extract(file, self.input_picture, map_preset=TXT_ONLY_PICTURE)
            except self.cmd.FFmpegError:
                pass
            try:
                self.cmd.extract(file, self.input_non_video, map_preset=TXT_ALL, map='-0:v')
            except self.cmd.FFmpegError:
                pass

        self.write_metadata()
        self.write_input_json()

    def write_metadata(self):
        with pushd_context(self.root):
            self.cmd.metadata_file(self.input_filepath, self.metadata_file)
            with open(self.metadata_file) as f:
                meta_lines = f.readlines()
            meta_lines = [line for line in meta_lines if line.partition('=')[0] not in
                          ('encoder', 'major_brand', 'minor_version', 'compatible_brands', 'compilation', 'media_type')]
            with open(self.metadata_file, 'w') as f:
                f.writelines(meta_lines)

    def write_input_json(self):
        d = self.input_data or {}
        prefix = self.input_prefix + '-'
        with pushd_context(self.root):
            seg_folders = [f for f in os.listdir('.') if os.path.isdir(f) and f.startswith(prefix)]
            for folder in seg_folders:
                d[folder] = {}
                with pushd_context(folder):
                    for f in os.listdir('.'):
                        d[folder][f] = excerpt_single_video_stream(f)
            for f in (self.input_picture, self.input_non_video):
                if os.path.isfile(f):
                    d[f] = ffmpeg.probe(f)
            self.input_data = d
            write_json_file(self.input_json, d, indent=4)

    def write_param(self):
        d = self.input_data
        if 'param' in d:
            args = []
            for arg in d['param']:
                args.append(shlex.quote(arg))
            with ensure_open_file(self.param_file, 'w') as f:
                f.write(' '.join(args))

    def read_input_json(self):
        with pushd_context(self.root):
            self.input_data = read_json_file(self.input_json)
        return self.input_data

    def tag(self):
        with pushd_context(self.root):
            with open(self.tag_file, 'w') as f:
                f.write(self.tag_sig)

    def has_tag(self) -> bool:
        with pushd_context(self.root):
            try:
                with open(self.tag_file) as f:
                    return f.readline().rstrip('\r\n') == self.tag_sig
            except FileNotFoundError:
                return False

    def has_segments(self) -> bool:
        return bool(self.read_input_json())

    def remove(self):
        shutil.rmtree(self.root)

    def set_param(self):
        ...
