#!/usr/bin/env python3
# encoding=utf8
import os
import random
import shutil
import subprocess
from time import sleep
from typing import Iterable, List, Iterator

import ffmpeg
import filetype

from .os_util import pushd_context, write_json_file, read_json_file, SlicedFileIO, ensure_open_file, fs_find_iter, \
    fs_rename, touch, shlex_join, shlex_double_quotes_join
from .tricks import get_logger, hex_hash, decorator_factory_args_choices, remove_from_list, seconds_from_colon_time

TXT_SEGMENT = 'segment'
TXT_NON_SEGMENT = 'non segment'
TXT_FILENAME = 'filename'
TXT_VIDEO = 'video'
TXT_OTHER = 'other'
TXT_MORE = 'more'
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


def get_real_duration(filepath: str) -> float:
    d = ffmpeg.probe(filepath)['format']
    duration = float(d['duration'])
    start_time = float(d.get('start_time', 0))
    return duration if start_time <= 0 else duration - start_time


class FFmpegArgumentList(list):
    def __init__(self, *args, **kwargs):
        super(FFmpegArgumentList, self).__init__()
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
            self.add_kwarg('-' + k.replace('__', ':'), v)
        return self


class FFmpegCommandCaller:
    logger = get_logger('ffmpeg.cmd')
    exe = 'ffmpeg'
    head = FFmpegArgumentList(exe)
    body = FFmpegArgumentList()
    to_pipe = False

    class FFmpegError(Exception):
        pass

    def __init__(self, banner: bool = True, loglevel: str = None, overwrite: bool = None, to_pipe: bool = False):
        self.to_pipe = to_pipe
        self.set_head(banner=banner, loglevel=loglevel, overwrite=overwrite)

    @property
    def cmd(self):
        return self.head + self.body

    def set_head(self, banner: bool = False, loglevel: str = None, verbose: str = None,
                 threads: int = None, overwrite: bool = None):
        h = FFmpegArgumentList(self.exe)
        if not banner:
            h.add('-hide_banner')
        if loglevel:
            h.add(loglevel=loglevel)
        if verbose:
            h.add(v=verbose)
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
        self.body = FFmpegArgumentList()

    def set_map_preset(self, map_preset: str):
        if not map_preset:
            return
        self.add_args(map=STREAM_MAP_PRESET_TABLE[map_preset])

    def proc_comm(self, input_bytes: bytes) -> tuple:
        cmd = self.cmd
        self.logger.info(shlex_double_quotes_join(cmd))
        if self.to_pipe:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        out, err = p.communicate(input_bytes)
        code = p.returncode
        if code:
            raise self.FFmpegError(code, (out or b'NOT CAPTURED').decode(), (err or b'NOT CAPTURED').decode())
        else:
            return (out or b'').decode(), (err or b'').decode()

    def proc_run(self) -> tuple:
        cmd = self.cmd
        self.logger.info(shlex_double_quotes_join(cmd))
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
    def concat(self, input_paths: Iterable[str] or Iterator[str], output_path: str, *output_opts,
               input_as_file: bool = False, extra_inputs: Iterable or Iterator = (),
               copy: bool = True, map_preset: str = None, **output_kwargs):
        self.reset_args()
        input_count = 0
        if input_as_file:
            concat_list = None
            self.add_args(safe=0, protocol_whitelist='file')
            for file in input_paths:
                input_count += 1
                self.add_args(f='concat', i=file)
        else:
            input_count += 1
            concat_list = '\n'.join(['file \'{}\''.format(e) for e in input_paths])
            self.add_args(f='concat', safe=0, protocol_whitelist='file,pipe', i='-')
        if extra_inputs:
            input_count += len(extra_inputs)
            self.add_args(i=extra_inputs)
        if copy:
            self.add_args(c='copy')
            self.add_args(map=range(input_count))
        self.set_map_preset(map_preset)
        self.add_args(*output_opts, **output_kwargs)
        self.add_args(output_path)
        if concat_list:
            return self.proc_comm(concat_list.encode())
        else:
            return self.proc_run()

    @decorator_choose_map_preset
    def segment(self, input_path: str, output_path: str = None, *output_opts,
                copy: bool = True, map_preset: str = None, **output_kwargs):
        self.reset_args()
        if not output_path:
            output_path = '%d' + os.path.splitext(input_path)[-1]
        self.add_args(i=input_path, f='segment')
        if copy:
            self.add_args(c='copy')
        self.set_map_preset(map_preset)
        self.add_args(*output_opts, **output_kwargs)
        self.add_args(output_path)
        return self.proc_run()

    def metadata_file(self, input_path: str, output_path: str):
        self.reset_args()
        self.add_args(i=input_path, f='ffmetadata')
        self.add_args(output_path)
        return self.proc_run()

    @decorator_choose_map_preset
    def convert(self, input_paths: Iterable[str] or Iterator[str], output_path: str,
                *output_opts,
                start: float or int or str = 0, end: float or int or str = None,
                copy: bool = False, map_preset: str = None,
                **output_kwargs):
        if isinstance(start, str):
            start = seconds_from_colon_time(start)
        if isinstance(end, str):
            end = seconds_from_colon_time(end)
        print(start, end)
        if start < 0:
            start = max([get_real_duration(f) for f in input_paths]) + start
        if end < 0:
            end = max([get_real_duration(f) for f in input_paths]) + end
        self.reset_args()
        print(start, end)

        if start:
            self.add_args(ss=start)

        self.add_args(i=input_paths)

        if end:
            self.add_args(t=end - start if start else end)

        if copy:
            self.add_args(map=range(len(input_paths)))
            self.add_args(c='copy')

        self.set_map_preset(map_preset)

        self.add_args(*output_opts, **output_kwargs)
        self.add_args(output_path)

        return self.proc_run()


class VideoSegmentsContainer:
    nickname = 'video_seg_con'
    logger = get_logger(nickname)
    ffmpeg_cmd = FFmpegCommandCaller(banner=False, loglevel='warning', overwrite=True)
    tag_file = 'VIDEO_SEGMENTS_CONTAINER.TAG'
    tag_sig = 'Signature: ' + hex_hash(tag_file.encode())
    picture_file = 'p.mp4'
    non_visual_file = 'nv.mkv'
    metadata_file = 'metadata.txt'
    concat_list_file = 'concat.txt'
    done_suffix = '.done'
    lock_suffix = '.lock'
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

    def __repr__(self):
        return "{} at '{}' from '{}'".format(VideoSegmentsContainer.__name__, self.root, self.input_filepath)

    def __init__(self, path: str, work_dir: str = None, map_video='V:0'):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise self.PathError("path not exist: '{}'".format(path))
        ss = map_video
        if len(ss) < 3:
            raise NotImplemented(map_video=ss)

        if os.path.isfile(path):
            self.input_filepath = path
            if filetype.guess(path).mime.startswith('video'):
                d, b = os.path.split(path)
                self.input_data = {TXT_FILENAME: b, TXT_SEGMENT: {}, TXT_NON_SEGMENT: {}}
                with SlicedFileIO(path) as f_cut:
                    fl_middle = len(f_cut) // 2
                    root_base = '.{}-{}'.format(self.nickname, hex_hash(
                        f_cut[:4096] + f_cut[fl_middle - 2048:fl_middle + 2048] + f_cut[:-4096])[:7])
                work_dir = work_dir or d
                path = self.root = os.path.join(work_dir, root_base)  # file path -> dir path
            else:
                raise self.PathError("non-video file: '{}'".format(path))

        if not os.path.isdir(path):
            try:
                os.makedirs(path, exist_ok=True)
            except FileExistsError:
                raise self.PathError("invalid folder path used by file: '{}'".format(path))
            self.tag()
            self.split_video(ss)

        if os.path.isdir(path):
            self.root = path
            if not self.is_tagged():
                raise self.ContainerError("non-container folder: '{}'".format(path))
            if not self.is_split():
                self.split_video(ss)
            self.read_input_json()
            if TXT_FILENAME not in self.input_data:
                self.read_filename()
            self.read_output_json()

    def write_filename(self):
        fn = self.input_data.get(TXT_FILENAME)
        if not fn:
            return
        with pushd_context(self.root):
            prefix = self.input_filename_prefix
            for f in fs_find_iter(pattern=prefix + '*', recursive=False, strip_root=True):
                fs_rename(f, prefix + fn, add_src_ext=False)
                break
            else:
                ensure_open_file(prefix + fn)

    def read_filename(self):
        with pushd_context(self.root):
            prefix = self.input_filename_prefix
            for f in fs_find_iter(pattern=prefix + '*', recursive=False, strip_root=True):
                filename = f.lstrip(prefix)
                self.input_data[TXT_FILENAME] = filename
                break
            else:
                raise self.ContainerError('no filename found')

    def split_video(self, select_streams='V:0'):
        i_file = self.input_filepath
        if not i_file:
            raise self.PathError('no source i_file path')
        d = self.input_data or {TXT_SEGMENT: {}, TXT_NON_SEGMENT: {}}

        with pushd_context(self.root):
            for stream in ffmpeg.probe(i_file, select_streams=select_streams)['streams']:
                index = stream['index']
                codec = stream['codec_name']
                suitable_filext = CODEC_NAME_TO_FILEXT_TABLE.get(codec)
                segment_output = '%d' + suitable_filext if suitable_filext else None
                index = str(index)
                d[TXT_SEGMENT][index] = {}
                seg_folder = self.input_prefix + index
                os.makedirs(seg_folder, exist_ok=True)
                with pushd_context(seg_folder):
                    self.ffmpeg_cmd.segment(i_file, segment_output, map='0:{}'.format(index))
            try:
                self.ffmpeg_cmd.extract(i_file, self.input_picture, map_preset=TXT_ONLY_PICTURE)
                d[TXT_NON_SEGMENT][self.picture_file] = {}
            except self.ffmpeg_cmd.FFmpegError:
                pass
            try:
                self.ffmpeg_cmd.extract(i_file, self.input_non_visual, map_preset=TXT_ALL, map='-0:v')
                d[TXT_NON_SEGMENT][self.non_visual_file] = {}
            except self.ffmpeg_cmd.FFmpegError:
                pass

        self.input_data = d
        self.write_metadata()
        self.write_input_json()

    def write_metadata(self):
        with pushd_context(self.root):
            self.ffmpeg_cmd.metadata_file(self.input_filepath, self.metadata_file)
            with open(self.metadata_file) as f:
                meta_lines = f.readlines()
            meta_lines = [line for line in meta_lines if line.partition('=')[0] not in
                          ('encoder', 'major_brand', 'minor_version', 'compatible_brands', 'compilation', 'media_type')]
            with open(self.metadata_file, 'w') as f:
                f.writelines(meta_lines)

    def write_input_json(self):
        d = self.input_data or {}
        prefix = self.input_prefix

        with pushd_context(self.root):
            for k in d[TXT_SEGMENT]:
                seg_folder = prefix + k
                d[TXT_SEGMENT][k] = {}
                with pushd_context(seg_folder):
                    for file in fs_find_iter(pattern=self.segment_filename_regex_pattern, regex=True,
                                             recursive=False, strip_root=True):
                        d[TXT_SEGMENT][k][file] = excerpt_single_video_stream(file)
            for k in d[TXT_NON_SEGMENT]:
                file = prefix + k
                if os.path.isfile(file):
                    d[TXT_NON_SEGMENT][k] = ffmpeg.probe(file)
                else:
                    del d[TXT_NON_SEGMENT][k]
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

    def tag(self):
        with pushd_context(self.root):
            with open(self.tag_file, 'w') as f:
                f.write(self.tag_sig)

    def is_tagged(self) -> bool:
        with pushd_context(self.root):
            try:
                with open(self.tag_file) as f:
                    return f.readline().rstrip('\r\n') == self.tag_sig
            except FileNotFoundError:
                return False

    def is_split(self) -> bool:
        return bool(self.read_input_json())

    def remove(self):
        shutil.rmtree(self.root)

    def set_output_args(self,
                        video_args: FFmpegArgumentList = None,
                        other_args: FFmpegArgumentList = None,
                        more_args: FFmpegArgumentList = None,
                        non_visual_map: List[str] = None,
                        filename: str = None):
        video_args = video_args or FFmpegArgumentList()
        other_args = other_args or FFmpegArgumentList()
        more_args = more_args or FFmpegArgumentList()
        non_visual_map = non_visual_map or []
        videos = self.input_data[TXT_SEGMENT].keys()
        others = self.input_data[TXT_NON_SEGMENT].keys()
        d = self.output_data or {}
        prefix = self.output_prefix

        d[TXT_SEGMENT] = video_args
        input_count = 0
        d[TXT_VIDEO] = []
        for index in videos:
            d[TXT_VIDEO].append(
                (os.path.join(prefix + index, self.concat_list_file), FFmpegArgumentList(map=input_count)))
            input_count += 1
        d[TXT_OTHER] = []
        for o in others:
            if o == self.non_visual_file:
                args = FFmpegArgumentList()
                for m in non_visual_map:
                    args.add(map='{}:{}'.format(input_count, m))
                if not non_visual_map:
                    args.add(map=input_count)
                args += other_args
                d[TXT_OTHER].append((prefix + o, args))
            else:
                d[TXT_OTHER].append((prefix + o, FFmpegArgumentList(map=input_count) + other_args))
            input_count += 1
        d[TXT_MORE] = FFmpegArgumentList(vcodec='copy') + more_args
        d[TXT_FILENAME] = filename or self.input_data[TXT_FILENAME]

        self.output_data = d
        self.write_output_json()
        self.write_output_concat_list_file()

    def write_output_concat_list_file(self):
        with pushd_context(self.root):
            d = self.input_data[TXT_SEGMENT]
            for index in d:
                folder = self.output_prefix + index
                os.makedirs(folder, exist_ok=True)
                with pushd_context(folder):
                    lines = ['file {}'.format(os.path.join(folder, seg)) for seg in
                             sorted(d[index].keys(), key=lambda x: int(os.path.splitext(x)[0]))]
                    with ensure_open_file(self.concat_list_file, 'w') as f:
                        f.write('\n'.join(lines))

    def output(self):
        if not self.read_output_json():
            raise self.ContainerError('no output config')
        if self.get_locked_segments_no_prefix() or \
                len(self.get_done_segments_no_prefix()) != len(self.get_all_segments_no_prefix()):
            raise self.ContainerError('not all segments converted')

    def check_file_has_lock(self, filepath):
        return os.path.isfile(filepath + self.lock_suffix)

    def check_file_has_done(self, filepath):
        return os.path.isfile(filepath + self.done_suffix)

    def get_all_segments_no_prefix(self):
        segments = []
        for i, d in self.input_data[TXT_SEGMENT]:
            segments.extend(os.path.join(i, f) for f in d)
        return segments

    def get_untouched_segments_no_prefix(self):
        all_segments = self.get_all_segments_no_prefix()
        lock_segments = self.get_locked_segments_no_prefix()
        done_segments = self.get_done_segments_no_prefix()
        return remove_from_list(remove_from_list(all_segments, lock_segments), done_segments)

    def get_locked_segments_no_prefix(self):
        segments = []
        prefix = self.output_prefix
        with pushd_context(self.root):
            for index in self.input_data[TXT_SEGMENT]:
                with pushd_context(prefix + index):
                    segments.extend([os.path.join(index, f.rstrip(self.lock_suffix)) for f in
                                     fs_find_iter('*' + self.lock_suffix)])
        return segments

    def get_done_segments_no_prefix(self):
        segments = []
        prefix = self.output_prefix
        with pushd_context(self.root):
            for index in self.input_data[TXT_SEGMENT]:
                with pushd_context(prefix + index):
                    segments.extend([os.path.join(index, f.rstrip(self.lock_suffix)) for f in
                                     fs_find_iter('*' + self.done_suffix)])
        return segments

    def output_segments_no_prefix(self):
        segments_no_prefix = self.get_untouched_segments_no_prefix()
        while segments_no_prefix:
            seg_path_no_prefix = random.choice(segments_no_prefix)
            self.convert_single_video_segment(seg_path_no_prefix)
            segments_no_prefix = self.get_untouched_segments_no_prefix()

    @staticmethod
    def random_sleep():
        sleep(random.uniform(0.3, 0.7))

    def convert_single_video_segment(self, segment_path_no_prefix):
        i_seg = self.input_prefix + segment_path_no_prefix
        o_seg = self.output_prefix + segment_path_no_prefix
        o_seg_lock = o_seg + self.lock_suffix
        o_seg_done = o_seg + self.done_suffix
        args = self.output_data[TXT_SEGMENT]
        with pushd_context(self.root):
            self.random_sleep()
            if self.check_file_has_lock(o_seg) or self.check_file_has_done(o_seg):
                return
            else:
                touch(o_seg_lock)
            try:
                self.ffmpeg_cmd.convert([i_seg], o_seg, *args)
                touch(o_seg_done)
                saved_error = None
            except Exception as e:
                saved_error = e
            finally:
                os.remove(o_seg_lock)
                if saved_error:
                    raise saved_error

    def convert_test_compression_ratio(self):
        pass
