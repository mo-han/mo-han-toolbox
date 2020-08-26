#!/usr/bin/env python3
# encoding=utf8
import json
import os
import random
import shutil
import subprocess
from time import sleep
from typing import Iterable, List, Iterator

import ffmpeg
import filetype

from .os_util import pushd_context, write_json_file, read_json_file, SubscriptableFileIO, ensure_open_file, \
    fs_find_iter, \
    fs_rename, fs_touch, shlex_double_quotes_join
from .tricks import hex_hash, decorator_factory_args_choices, remove_from_list, seconds_from_colon_time, \
    dedup_list
from .log import get_logger

S_SEGMENT = 'segment'
S_NON_SEGMENT = 'non segment'
S_FILENAME = 'filename'
S_VIDEO = 'video'
S_OTHER = 'other'
S_MORE = 'more'
S_ALL = 'all'
S_ONLY_VIDEO = 'only video'
S_ONLY_PICTURE = 'only picture'
S_ONLY_AUDIO = 'only audio'
S_ONLY_SUBTITLE = 'only subtitle'
S_ONLY_DATA = 'only data'
S_ONLY_ATTACHMENT = 'only attachment'
S_NO_VIDEO = 'no video'
S_NO_AUDIO = 'no audio'
S_NO_SUBTITLE = 'no subtitle'
S_NO_DATA = 'no data'
S_NO_ATTACHMENT = 'no attachment'
S_FIRST_VIDEO = 'first video'
STREAM_MAP_PRESET_TABLE = {S_ALL: ['0'], S_ONLY_VIDEO: ['0:V'], S_ONLY_AUDIO: ['0:a'],
                           S_ONLY_SUBTITLE: ['0:s'], S_ONLY_ATTACHMENT: ['0:t'], S_ONLY_DATA: ['0:d'],
                           S_NO_VIDEO: ['0', '-0:V'], S_NO_AUDIO: ['0', '-0:a'], S_NO_SUBTITLE: ['0', '-0:s'],
                           S_NO_ATTACHMENT: ['0', '-0:t'], S_NO_DATA: ['0', '-0:d'],
                           S_FIRST_VIDEO: ['0:V:0'], S_ONLY_PICTURE: ['0:v', '-0:V']}
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
    file_format = data['format']
    streams = data['streams']
    if len(streams) == 1:
        single_stream = streams[0]
        if single_stream['codec_type'] == 'video' and single_stream['disposition']['attached_pic'] == 0:
            d['size'] = int(file_format['size'])
            try:
                d['start_time'] = start_time = float(single_stream.get('start_time', file_format['start_time']))
                duration = float(single_stream.get('duration', file_format['duration']))
                d['duration'] = round((duration - start_time), 6)
            except KeyError:
                d['duration'] = float(file_format['duration'])
            d['bit_rate'] = int(8 * d['size'] // d['duration'])
            d['codec_name'] = single_stream['codec_name']
            d['height'] = single_stream['height']
            d['with'] = single_stream['width']
            d['pix_fmt'] = single_stream['pix_fmt']
    return d


def get_real_duration(filepath: str) -> float:
    d = ffmpeg.probe(filepath)['format']
    duration = float(d['duration'])
    start_time = float(d.get('start_time', 0))
    return duration if start_time <= 0 else duration - start_time


class FFmpegArgsList(list):
    def __init__(self, *args, **kwargs):
        super(FFmpegArgsList, self).__init__()
        self.add(*args, **kwargs)

    def add_arg(self, arg):
        if isinstance(arg, str):
            self.append(arg)
        elif isinstance(arg, (Iterable, Iterator)):
            for a in arg:
                self.add_arg(a)
        else:
            self.append(str(arg))
        return self

    def add_kwarg(self, key: str, value):
        if isinstance(key, str):
            if isinstance(value, str):
                self.append(key)
                self.append(value)
            elif isinstance(value, (Iterable, Iterator)):
                for v in value:
                    self.add_kwarg(key, v)
            elif value is True:
                self.append(key)
            elif value is None or value is False:
                pass
            else:
                self.append(key)
                self.append(str(value))
        return self

    def add(self, *args, **kwargs):
        for a in args:
            self.add_arg(a)
        for k, v in kwargs.items():
            if k in ('x265_params',):
                self.add_kwarg('-' + k.replace('_', '-'), v)
            else:
                self.add_kwarg('-' + k.replace('__', ':'), v)
        return self


class FFmpegCaller:
    exe = 'ffmpeg'
    head = FFmpegArgsList(exe)
    body = FFmpegArgsList()
    capture_stdout_stderr = False

    class FFmpegError(Exception):
        pass

    def __init__(self, banner: bool = True, loglevel: str = None, overwrite: bool = None, to_pipe: bool = False):
        self.logger = get_logger('.'.join((__name__, self.__class__.__name__)))
        self.capture_stdout_stderr = to_pipe
        self.set_head(banner=banner, loglevel=loglevel, overwrite=overwrite)

    @property
    def cmd(self):
        return self.head + self.body

    def set_head(self, banner: bool = False, loglevel: str = None, threads: int = None, overwrite: bool = None):
        h = FFmpegArgsList(self.exe)
        if not banner:
            h.add('-hide_banner')
        if loglevel:
            h.add(loglevel=loglevel)
        if overwrite is True:
            h.add('-y')
        elif overwrite is False:
            h.add('-n')
        if threads:
            h.add(threads=threads)
        self.head = h

    def add_args(self, *args, **kwargs):
        self.body.add(*args, **kwargs)

    def reset_args(self):
        self.body = FFmpegArgsList()

    def set_map_preset(self, map_preset: str):
        if not map_preset:
            return
        self.add_args(map=STREAM_MAP_PRESET_TABLE[map_preset])

    def proc_comm(self, input_bytes: bytes) -> bytes:
        cmd = self.cmd
        self.logger.info(shlex_double_quotes_join(cmd))
        if self.capture_stdout_stderr:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        out, err = p.communicate(input_bytes)
        code = p.returncode
        if code:
            raise self.FFmpegError(code, (err or b'<UNCAUGHT>').decode())
        else:
            if err:
                self.logger.debug(err.decode())
            return out or b''

    def proc_run(self) -> bytes:
        cmd = self.cmd
        self.logger.info(shlex_double_quotes_join(cmd))
        if self.capture_stdout_stderr:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p = subprocess.run(cmd)
        code = p.returncode
        if code:
            raise self.FFmpegError(code, (p.stderr or b'<UNCAUGHT>').decode())
        else:
            if p.stderr:
                self.logger.debug(p.stderr.decode())
            return p.stdout or b''

    @decorator_choose_map_preset
    def concat(self, input_paths: Iterable[str] or Iterator[str], output_path: str,
               output_args: Iterable[str] or Iterator[str] = (), *,
               concat_demuxer: bool = False, extra_inputs: Iterable or Iterator = (),
               start: float or int or str = 0, end: float or int or str = 0,
               copy_all: bool = True, map_preset: str = None, metadata_file: str = None,
               **output_kwargs):
        if isinstance(start, str):
            start = seconds_from_colon_time(start)
        if isinstance(end, str):
            end = seconds_from_colon_time(end)
        if start < 0:
            start = max([get_real_duration(f) for f in input_paths]) + start
        if end < 0:
            end = max([get_real_duration(f) for f in input_paths]) + end
        self.reset_args()
        if start:
            self.add_args(ss=start)
        input_count = 0
        if concat_demuxer:
            concat_list = None
            for file in input_paths:
                input_count += 1
                self.add_args(safe=0, protocol_whitelist='file', f='concat', i=file)
        else:
            input_count += 1
            concat_list = '\n'.join(['file \'{}\''.format(e) for e in input_paths])
            self.add_args(f='concat', safe=0, protocol_whitelist='file,pipe', i='-')
        if extra_inputs:
            input_count += len(extra_inputs)
            self.add_args(i=extra_inputs)
        if metadata_file:
            self.add_args(i=metadata_file, map_metadata=input_count)
        if end:
            self.add_args(t=end - start if start else end)
        if copy_all:
            self.add_args(c='copy')
            if not map_preset:
                self.add_args(map=range(input_count))
        self.set_map_preset(map_preset)
        self.add_args(*output_args, **output_kwargs)
        self.add_args(output_path)
        if concat_list:
            return self.proc_comm(concat_list.encode())
        else:
            return self.proc_run()

    @decorator_choose_map_preset
    def segment(self, input_path: str, output_path: str = None,
                output_args: Iterable[str] or Iterator[str] = (), *,
                copy: bool = True, reset_time: bool = True,
                map_preset: str = None, **output_kwargs):
        self.reset_args()
        if not output_path:
            output_path = '%d' + os.path.splitext(input_path)[-1]
        self.add_args(i=input_path, f='segment')
        if copy:
            self.add_args(c='copy')
        if reset_time:
            self.add_args(reset_timestamps=1)
        self.set_map_preset(map_preset)
        self.add_args(*output_args, **output_kwargs)
        self.add_args(output_path)
        return self.proc_run()

    def metadata_file(self, input_path: str, output_path: str):
        self.reset_args()
        self.add_args(i=input_path, f='ffmetadata')
        self.add_args(output_path)
        return self.proc_run()

    @decorator_choose_map_preset
    def convert(self, input_paths: Iterable[str] or Iterator[str], output_path: str,
                output_args: Iterable[str] or Iterator[str] = (), *,
                start: float or int or str = 0, end: float or int or str = 0,
                copy_all: bool = False, map_preset: str = None, metadata_file: str = None,
                **output_kwargs):
        if isinstance(start, str):
            start = seconds_from_colon_time(start)
        if isinstance(end, str):
            end = seconds_from_colon_time(end)
        if start < 0:
            start = max([get_real_duration(f) for f in input_paths]) + start
        if end < 0:
            end = max([get_real_duration(f) for f in input_paths]) + end
        self.reset_args()

        if start:
            self.add_args(ss=start)
        self.add_args(i=input_paths)
        if metadata_file:
            self.add_args(i=metadata_file, map_metadata=len(input_paths))
        if end:
            self.add_args(t=end - start if start else end)

        if copy_all:
            self.add_args(c='copy')
            if not map_preset:
                self.add_args(map=len(input_paths) - 1)
        self.set_map_preset(map_preset)
        self.add_args(*output_args, **output_kwargs)
        self.add_args(output_path)
        return self.proc_run()


class FFmpegSegmentsContainer:
    nickname = 'ffsegcon'
    logger = get_logger('.'.join((__name__, nickname)))
    ffcmd = FFmpegCaller(banner=False, loglevel='warning', overwrite=True)
    tag_file = 'FFMPEG_SEGMENTS_CONTAINER.TAG'
    tag_sig = 'Signature: ' + hex_hash(tag_file.encode())
    picture_file = 'p.mp4'
    non_visual_file = 'nv.mkv'
    test_json = 't.json'
    metadata_file = 'metadata.txt'
    concat_list_file = 'concat.txt'
    suffix_done = '.DONE'
    suffix_lock = '.LOCK'
    suffix_delete = '.DELETE'
    segment_filename_regex_pattern = r'^\d+\.[^.]+'
    input_filename_prefix = 'i='
    input_json = 'i.json'
    input_prefix = 'i-'
    input_picture = input_prefix + picture_file
    input_non_visual = input_prefix + non_visual_file
    input_filepath = None
    input_data = None
    output_filename_prefix = 'o='
    output_prefix = 'o-'
    output_json = 'o.json'
    output_data = None

    class PathError(Exception):
        pass

    class ContainerError(Exception):
        pass

    class SegmentLockedError(Exception):
        pass

    class SegmentNotDoneError(Exception):
        pass

    class SegmentDeleteRequest(Exception):
        pass

    class SegmentMissing(Exception):
        pass

    def __repr__(self):
        return "{} at '{}' from '{}'".format(FFmpegSegmentsContainer.__name__, self.root, self.input_filepath)

    def __init__(self, path: str, work_dir: str = None, single_video_stream: bool = True):
        path = os.path.abspath(path)
        select_streams = 'V:0' if single_video_stream else 'V'
        if not os.path.exists(path):
            raise self.PathError("path not exist: '{}'".format(path))

        if os.path.isfile(path):
            self.input_filepath = path
            if filetype.guess(path).mime.startswith('video'):
                d, b = os.path.split(path)
                self.input_data = {S_FILENAME: b, S_SEGMENT: {}, S_NON_SEGMENT: {}}
                with SubscriptableFileIO(path) as f:
                    middle = f.size // 2
                    root_base = '.{}-{}'.format(self.nickname, hex_hash(
                        f[:4096] + f[middle - 2048:middle + 2048] + f[-4096:])[:8])
                work_dir = work_dir or d
                path = self.root = os.path.join(work_dir, root_base)  # file path -> dir path
            else:
                raise self.PathError("non-video file: '{}'".format(path))

        if not os.path.isdir(path):
            try:
                os.makedirs(path, exist_ok=True)
            except FileExistsError:
                raise self.PathError("invalid folder path used by file: '{}'".format(path))
            self.tag_container_folder()
            self.split(select_streams=select_streams)

        if os.path.isdir(path):
            self.root = path
            if not self.container_is_tagged():
                raise self.ContainerError("non-container folder: '{}'".format(path))
            if not self.is_split():
                self.split(select_streams=select_streams)
            self.read_input_json()
            if S_FILENAME not in self.input_data:
                self.read_filename()
            self.read_output_json()

    def write_filename(self):
        fn = self.input_data.get(S_FILENAME)
        if not fn:
            return
        with pushd_context(self.root):
            prefix = self.input_filename_prefix
            for f in fs_find_iter(pattern=prefix + '*', recursive=False, strip_root=True):
                fs_rename(f, prefix + fn, append_src_ext=False)
                break
            else:
                ensure_open_file(prefix + fn)

    def read_filename(self):
        with pushd_context(self.root):
            prefix = self.input_filename_prefix
            for f in fs_find_iter(pattern=prefix + '*', recursive=False, strip_root=True):
                filename = f.lstrip(prefix)
                self.input_data[S_FILENAME] = filename
                return filename
            else:
                raise self.ContainerError('no filename found')

    def split(self, select_streams='V:0'):
        i_file = self.input_filepath
        if not i_file:
            raise self.ContainerError('no input filepath')
        d = self.input_data or {S_SEGMENT: {}, S_NON_SEGMENT: {}}

        with pushd_context(self.root):
            for stream in ffmpeg.probe(i_file, select_streams=select_streams)['streams']:
                index = stream['index']
                # codec = stream['codec_name']
                # suitable_filext = CODEC_NAME_TO_FILEXT_TABLE.get(codec)
                # segment_output = '%d' + suitable_filext if suitable_filext else None
                segment_output = '%d.mkv'
                index = str(index)
                d[S_SEGMENT][index] = {}
                seg_folder = self.input_prefix + index
                os.makedirs(seg_folder, exist_ok=True)
                with pushd_context(seg_folder):
                    self.ffcmd.segment(i_file, segment_output, map='0:{}'.format(index))
            try:
                self.ffcmd.convert([i_file], self.input_picture, copy_all=True, map_preset=S_ONLY_PICTURE)
                d[S_NON_SEGMENT][self.picture_file] = {}
            except self.ffcmd.FFmpegError:
                pass
            try:
                self.ffcmd.convert([i_file], self.input_non_visual, copy_all=True, map_preset=S_ALL, map='-0:v')
                d[S_NON_SEGMENT][self.non_visual_file] = {}
            except self.ffcmd.FFmpegError:
                pass

        self.input_data = d
        self.write_metadata()
        self.write_input_json()

    def write_metadata(self):
        with pushd_context(self.root):
            self.ffcmd.metadata_file(self.input_filepath, self.metadata_file)
            with open(self.metadata_file, encoding='utf8') as f:
                meta_lines = f.readlines()
            meta_lines = [line for line in meta_lines if line.partition('=')[0] not in
                          ('encoder', 'major_brand', 'minor_version', 'compatible_brands', 'compilation', 'media_type')]
            with open(self.metadata_file, 'w', encoding='utf8') as f:
                f.writelines(meta_lines)

    def write_input_json(self):
        d = self.input_data or {}
        prefix = self.input_prefix

        with pushd_context(self.root):
            for k in d[S_SEGMENT]:
                seg_folder = prefix + k
                d[S_SEGMENT][k] = {}
                with pushd_context(seg_folder):
                    for file in fs_find_iter(pattern=self.segment_filename_regex_pattern, regex=True,
                                             recursive=False, strip_root=True):
                        d[S_SEGMENT][k][file] = excerpt_single_video_stream(file)
            for k in d[S_NON_SEGMENT]:
                file = prefix + k
                if os.path.isfile(file):
                    d[S_NON_SEGMENT][k] = ffmpeg.probe(file)
                else:
                    del d[S_NON_SEGMENT][k]
            write_json_file(self.input_json, d, indent=4)

        self.input_data = d

    def read_input_json(self):
        with pushd_context(self.root):
            self.input_data = read_json_file(self.input_json)
        self.write_filename()
        return self.input_data

    def read_output_json(self):
        with pushd_context(self.root):
            self.output_data = read_json_file(self.output_json)
        return self.output_data

    def write_output_json(self):
        with pushd_context(self.root):
            write_json_file(self.output_json, self.output_data, indent=4)

    def tag_container_folder(self):
        with pushd_context(self.root):
            with open(self.tag_file, 'w') as f:
                f.write(self.tag_sig)

    def container_is_tagged(self) -> bool:
        with pushd_context(self.root):
            try:
                with open(self.tag_file) as f:
                    return f.readline().rstrip('\r\n') == self.tag_sig
            except FileNotFoundError:
                return False

    def is_split(self) -> bool:
        return bool(self.read_input_json())

    def purge(self):
        shutil.rmtree(self.root)
        self.__dict__ = {}

    def config(self,
               video_args: FFmpegArgsList = None,
               other_args: FFmpegArgsList = None,
               more_args: FFmpegArgsList = None,
               non_visual_map: Iterable[str] or Iterator[str] = (),
               filename: str = None,
               **kwargs):
        video_args = video_args or FFmpegArgsList()
        other_args = other_args or FFmpegArgsList()
        more_args = more_args or FFmpegArgsList()
        videos = self.input_data[S_SEGMENT].keys()
        others = self.input_data[S_NON_SEGMENT].keys()
        need_map = True if len(videos) > 1 or self.picture_file in others else False
        d = self.output_data or {}
        d['original'] = {'video_args': video_args,
                         'other_args': other_args,
                         'more_args': more_args,
                         'non_visual_map': non_visual_map,
                         'filename': filename,
                         'kwargs': kwargs}
        input_count = 0

        d[S_VIDEO] = []
        for index in videos:
            args = FFmpegArgsList()
            if need_map:
                args.add(map=input_count)
            i_args = os.path.join(self.output_prefix + index, self.concat_list_file), args
            d[S_VIDEO].append(i_args)
            input_count += 1

        d[S_OTHER] = []
        for o in others:
            args = FFmpegArgsList()
            if o == self.non_visual_file:
                if non_visual_map:
                    for m in non_visual_map:
                        if m.startswith('-'):
                            args.add(map='-{}:{}'.format(input_count, m.lstrip('-')))
                        else:
                            args.add(map='{}:{}'.format(input_count, m))
                elif need_map:
                    args.add(map=input_count)
                args += other_args
                i_args = self.input_prefix + o, args
                d[S_OTHER].append(i_args)
            else:
                if need_map:
                    args.add(map=input_count)
                i_args = self.input_prefix + o, args
                d[S_OTHER].append(i_args)
            input_count += 1

        d[S_SEGMENT] = video_args
        d[S_MORE] = FFmpegArgsList(vcodec='copy') + more_args
        d[S_FILENAME] = filename or self.input_data[S_FILENAME]
        d['kwargs'] = kwargs

        self.output_data = d
        self.write_output_json()
        self.write_output_concat_list_file()

    def config_video(self, video_args: FFmpegArgsList = None, crf: int = None):
        conf = self.read_output_json()
        video_args = video_args or FFmpegArgsList()
        if crf is not None:
            video_args.add(crf=crf)
        conf['original']['video_args'] = video_args
        self.config(**conf['original'])

    def config_hevc(self, video_args: FFmpegArgsList = None, crf: int = None,
                    x265_log_level: str = 'error', **x265_params):
        conf = self.read_output_json()
        video_args = video_args or FFmpegArgsList()
        if crf is not None:
            video_args.add(crf=crf)
        x265_params_s = f'log-level={x265_log_level}'
        for k in x265_params:
            k_s = k.replace('_', '-')
            x265_params_s += f':{k_s}={x265_params[k]}'
        video_args.add(vcodec='hevc', x265_params=f'{x265_params_s}')
        conf['original']['video_args'] = video_args
        self.config(**conf['original'])

    def config_qsv264(self, video_args: FFmpegArgsList = None, crf: int = None):
        conf = self.read_output_json()
        video_args = video_args or FFmpegArgsList()
        video_args.add(vcodec='h264_qsv')
        if crf is not None:
            video_args.add(global_quality=crf)
        conf['original']['video_args'] = video_args
        self.config(**conf['original'])

    def merge(self):
        if not self.read_output_json():
            raise self.ContainerError('no output config')
        if self.get_lock_segments() or \
                len(self.get_done_segments()) != len(self.get_all_segments()):
            raise self.SegmentMissing
        d = self.output_data
        concat_list = []
        extra_input_list = []
        output_args = []
        for i, args in d[S_VIDEO]:
            concat_list.append(i)
            output_args.extend(args)
        for i, args in d[S_OTHER]:
            extra_input_list.append(i)
            output_args.extend(args)
        output_args.extend(d[S_MORE])
        with pushd_context(self.root):
            self.ffcmd.concat(concat_list, d[S_FILENAME], output_args,
                              concat_demuxer=True, extra_inputs=extra_input_list, copy_all=False,
                              metadata_file=self.metadata_file,
                              **d['kwargs'])

    def write_output_concat_list_file(self):
        with pushd_context(self.root):
            d = self.input_data[S_SEGMENT]
            for index in d:
                folder = self.output_prefix + index
                os.makedirs(folder, exist_ok=True)
                with pushd_context(folder):
                    lines = ["file '{}'".format(os.path.join(folder, seg)) for seg in
                             sorted(d[index].keys(), key=lambda x: int(os.path.splitext(x)[0]))]
                    with ensure_open_file(self.concat_list_file, 'w') as f:
                        f.write('\n'.join(lines))

    def file_has_lock(self, filepath):
        return os.path.isfile(filepath + self.suffix_lock)

    def file_has_done(self, filepath):
        return os.path.isfile(filepath + self.suffix_done)

    def file_has_delete(self, filepath):
        return os.path.isfile(filepath + self.suffix_delete)

    def get_all_segments(self):
        segments = []
        for i, d in self.input_data[S_SEGMENT].items():
            segments.extend((i, f) for f in d)
        return segments

    def get_untouched_segments(self):
        all_segments = self.get_all_segments()
        lock_segments = self.get_lock_segments()
        done_segments = self.get_done_segments()
        return remove_from_list(remove_from_list(all_segments, lock_segments), done_segments)

    def get_lock_segments(self):
        segments = []
        prefix = self.output_prefix
        with pushd_context(self.root):
            for index in self.input_data[S_SEGMENT]:
                with pushd_context(prefix + index):
                    segments.extend([(index, f.rstrip(self.suffix_lock)) for f in
                                     fs_find_iter('*' + self.suffix_lock)])
        return segments

    def get_done_segments(self):
        segments = []
        prefix = self.output_prefix
        with pushd_context(self.root):
            for index in self.input_data[S_SEGMENT]:
                with pushd_context(prefix + index):
                    segments.extend([(index, f.rstrip(self.suffix_done)) for f in
                                     fs_find_iter('*' + self.suffix_done)])
        return segments

    def convert(self, overwrite: bool = False):
        segments = self.get_untouched_segments()
        while segments:
            stream_id, segment_file = random.choice(segments)
            self.convert_one_segment(stream_id, segment_file, overwrite=overwrite)
            segments = self.get_untouched_segments()

    def convert_overwrite(self):
        self.convert(overwrite=True)

    def nap(self):
        t = round(random.uniform(0.2, 0.4), 3)
        self.logger.debug('sleep {}s'.format(t))
        sleep(t)

    def file_tag_lock(self, filepath):
        if self.file_has_lock(filepath) or self.file_has_done(filepath):
            return
        else:
            fs_touch(filepath + self.suffix_lock)

    def file_tag_unlock(self, filepath):
        if self.file_has_lock(filepath):
            os.remove(filepath + self.suffix_lock)

    def file_tag_done(self, filepath):
        if self.file_has_done(filepath):
            return
        if self.file_has_lock(filepath):
            fs_rename(filepath + self.suffix_lock, filepath + self.suffix_done,
                      stay_in_src_dir=False, append_src_ext=False)

    def file_tag_delete(self, filepath):
        fs_touch(filepath + self.suffix_delete)

    def convert_one_segment(self, stream_id, segment_file, overwrite=False) -> dict:
        segment_path_no_prefix = os.path.join(stream_id, segment_file)
        i_seg = self.input_prefix + segment_path_no_prefix
        o_seg = self.output_prefix + segment_path_no_prefix
        args = self.output_data[S_SEGMENT]
        with pushd_context(self.root):
            self.nap()
            if self.file_has_lock(o_seg):
                raise self.SegmentLockedError
            if not overwrite and self.file_has_done(o_seg):
                return self.get_done_segment_info(filepath=o_seg)
            self.file_tag_lock(o_seg)
            try:
                saved_error = None
                self.ffcmd.convert([i_seg], o_seg, args)
                self.nap()
                if self.file_has_delete(o_seg):
                    self.logger.info('delete {}'.format(o_seg))
                    os.remove(o_seg)
                    raise self.SegmentDeleteRequest
                else:
                    self.file_tag_done(o_seg)
                    return self.get_done_segment_info(filepath=o_seg)
            except Exception as e:
                saved_error = e
            finally:
                self.file_tag_unlock(o_seg)
                if saved_error:
                    raise saved_error

    def get_done_segment_info(self, stream_id=None, segment_filename=None, filepath=None) -> dict:
        if filepath:
            o_seg = filepath
        else:
            o_seg = os.path.join(self.output_prefix + stream_id, segment_filename)
        with pushd_context(self.root):
            if not self.file_has_done(o_seg):
                raise self.SegmentNotDoneError
            return excerpt_single_video_stream(o_seg)

    def estimate_overwrite(self):
        return self.estimate(overwrite=True)

    def estimate(self, overwrite=False) -> dict:
        d = {}
        segments = self.input_data[S_SEGMENT]
        for stream_id in segments:
            d[stream_id] = sd = {}
            segments_sorted_by_rate = sorted([(k, v) for k, v in segments[stream_id].items() if v['duration'] >= 1],
                                             key=lambda x: x[-1]['bit_rate'])
            min_rate_seg_f, min_rate_seg_d = segments_sorted_by_rate[0]
            max_rate_seg_f, max_rate_seg_d = segments_sorted_by_rate[-1]
            sd['min'] = {'file': min_rate_seg_f, 'input': min_rate_seg_d,
                         'output': self.convert_one_segment(stream_id, min_rate_seg_f,
                                                            overwrite=overwrite)}
            sd['max'] = {'file': max_rate_seg_f, 'input': max_rate_seg_d,
                         'output': self.convert_one_segment(stream_id, max_rate_seg_f,
                                                            overwrite=overwrite)}
            sd['min']['ratio'] = round(sd['min']['output']['bit_rate'] / sd['min']['input']['bit_rate'], 3)
            sd['max']['ratio'] = round(sd['max']['output']['bit_rate'] / sd['max']['input']['bit_rate'], 3)

            k = (sd['max']['output']['bit_rate'] - sd['min']['output']['bit_rate']) / (
                    sd['max']['input']['bit_rate'] - sd['min']['input']['bit_rate'])

            def linear_estimate(input_bit_rate):
                return k * (input_bit_rate - sd['min']['input']['bit_rate']) + sd['min']['output']['bit_rate']

            total_duration = 0
            total_input_size = 0
            estimated_output_size = 0
            for seg_d in segments[stream_id].values():
                estimated_bit_rate = linear_estimate(seg_d['bit_rate'])
                duration = seg_d['duration']
                total_duration += duration
                total_input_size += seg_d['size']
                estimated_output_size += duration * estimated_bit_rate // 8
            sd['estimate'] = {'type': 'linear',
                              'size': int(estimated_output_size),
                              'duration': total_duration,
                              'bit_rate': 8 * estimated_output_size // total_duration,
                              'ratio': round(estimated_output_size / total_input_size, 3)}

        with pushd_context(self.root):
            write_json_file(self.test_json, d, indent=4)
        return {k: v['estimate']['ratio'] for k, v in d.items()}

    def clear(self):
        with pushd_context(self.root):
            segments = self.get_lock_segments() + self.get_done_segments()
            while segments:
                for i, seg in segments:
                    o_seg = os.path.join(self.output_prefix + i, seg)
                    if not os.path.isfile(o_seg):
                        continue
                    elif self.file_has_done(o_seg):
                        self.logger.info('delete done segment {}'.format(o_seg))
                        os.remove(o_seg)
                        os.remove(o_seg + self.suffix_done)
                    elif self.file_has_lock(o_seg):
                        self.logger.info('request delete locked segment {}'.format(o_seg))
                        fs_touch(o_seg + self.suffix_delete)
                    else:
                        self.logger.info('delete stub segment{}'.format(o_seg))
                        os.remove(o_seg)
                        if self.file_has_delete(o_seg):
                            os.remove(o_seg + self.suffix_delete)
                segments = self.get_lock_segments() + self.get_done_segments()
