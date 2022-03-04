#!/usr/bin/env python3
# encoding=utf8
import fnmatch
import shutil
import shutil as patched_shutil
from glob import glob
from queue import Queue
from shutil import Error
from typing import Callable, Generator

from mylib.easy import *
from ezpykit.enhance_stdlib.shutil.__deprecated__ import FileToDirectoryError, DirectoryToFileError, \
    NeitherFileNorDirectoryError
from mylib.ext import fstk
from mylib.ext.ostk import Clipboard


def fs_find_iter(pattern: str or Callable = None, root: str = '.',
                 regex: bool = False, find_dir_instead_of_file: bool = False,
                 recursive: bool = True, strip_root: bool = True,
                 progress_queue: Queue = None) -> Generator:
    if find_dir_instead_of_file:
        def pick_os_walk_tuple(parent, folder_list, file_list):
            return parent, folder_list

        def check(x):
            return os.path.isdir(x)
    else:
        def pick_os_walk_tuple(parent, folder_list, file_list):
            return parent, file_list

        def check(x):
            return os.path.isfile(x)

    if strip_root:
        def join_path(path, *paths):
            return relative_join_path(path, *paths, start_path=root)
    else:
        join_path = os.path.join

    if pattern is None:
        def match(fname):
            return True
    elif isinstance(pattern, str):
        if regex:
            def match(fname):
                if re.search(pattern, fname):
                    return True
                else:
                    return False
        else:
            def match(fname):
                return fnmatch.fnmatch(fname, pattern)
    elif isinstance(pattern, Callable):
        match = pattern
    else:
        raise ValueError("invalid pattern: '{}', should be `str` or `function(fname)`")

    def put_progress(path):
        progress_queue.put(path)

    def no_progress(path):
        pass

    if progress_queue:
        update_progress = put_progress
    else:
        update_progress = no_progress

    if recursive:
        for t3e in os.walk(root):
            par, fn_list = pick_os_walk_tuple(*t3e)
            for fn in fn_list:
                if match(fn):
                    output_path = join_path(par, fn)
                    update_progress(output_path)
                    yield output_path
    else:
        for basename in os.listdir(root):
            real_path = os.path.join(root, basename)
            output_path = join_path(root, basename)
            if check(real_path) and match(basename):
                update_progress(output_path)
                yield output_path


def real_join_path(path, *paths, expanduser: bool = True, expandvars: bool = True):
    """realpath(join(...))"""
    if expanduser:
        path = os.path.expanduser(path)
        paths = [os.path.expanduser(p) for p in paths]
    if expandvars:
        path = os.path.expandvars(path)
        paths = [os.path.expandvars(p) for p in paths]
    return os.path.realpath(os.path.join(path, *paths))


def relative_join_path(path, *paths, start_path: str = None, expanduser: bool = True, expandvars: bool = True):
    """relpath(join(...))"""
    if expanduser:
        path = os.path.expanduser(path)
        paths = [os.path.expanduser(p) for p in paths]
    if expandvars:
        path = os.path.expandvars(path)
        paths = [os.path.expandvars(p) for p in paths]
    return os.path.relpath(os.path.join(path, *paths), start=start_path)


def fs_inplace_rename(src: str, pattern: str, replace: str, only_basename: bool = True, dry_run: bool = False):
    """DEPRECATED NO MORE DEVELOPMENT"""
    if only_basename:
        parent, basename = os.path.split(src)
        dst = os.path.join(parent, basename.replace(pattern, replace))
    else:
        dst = src.replace(pattern, replace)
    if src != dst:
        print('* {} ->\n  {}'.format(src, dst))
    if not dry_run:
        shutil.move(src, dst)


def fs_inplace_rename_regex(src: str, pattern: str, replace: str, only_basename: bool = True, dry_run: bool = False):
    """DEPRECATED NO MORE DEVELOPMENT"""
    if only_basename:
        parent, basename = os.path.split(src)
        dst = os.path.join(parent, re.sub(pattern, replace, basename))
    else:
        dst = re.sub(pattern, replace, src)
    if src != dst:
        print('* {} ->\n  {}'.format(src, dst))
    if not dry_run:
        shutil.move(src, dst)


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


VIDEO_FILE_EXTENSIONS = ['.mp4', '.m4v', '.mkv', '.flv', '.webm']


def list_files(src: str or T.Iterable or Clipboard, recursive=False, progress_queue: Queue = None) -> T.List[str]:
    common_kwargs = dict(recursive=recursive, progress_queue=progress_queue)
    # if src is None:
    #     return list_files(clipboard.list_paths(exist_only=True), recursive=recursive)
    # elif isinstance(src, str):
    if isinstance(src, str):
        if os.path.isfile(src):
            return [src]
        elif os.path.isdir(src):
            # print(src)
            return list(fstk.find_iter('f', src, recursive=True))
        else:
            return [fp for fp in glob(src, recursive=recursive) if os.path.isfile(fp)]
    elif isinstance(src, T.Iterable):
        r = []
        for s in src:
            r.extend(list_files(s, **common_kwargs))
        return r
    elif isinstance(src, Clipboard):
        return list_files(src.list_path(exist_only=True), **common_kwargs)
    else:
        raise TypeError('invalid source', src)


def list_dirs(src: str or T.Iterable or Clipboard, recursive=False, progress_queue: Queue = None) -> list:
    common_kwargs = dict(recursive=recursive, progress_queue=progress_queue)
    if isinstance(src, str):
        if os.path.isdir(src):
            dirs = [src]
            if recursive:
                dirs.extend(
                    list(fstk.find_iter('d', src, recursive=True)))
            return dirs
        else:
            return [p for p in glob(src, recursive=recursive) if os.path.isdir(p)]
    elif isinstance(src, T.Iterable):
        dirs = []
        for s in src:
            dirs.extend(list_dirs(s, **common_kwargs))
        return dirs
    elif isinstance(src, Clipboard):
        return list_dirs(src.list_path(exist_only=True), **common_kwargs)
    else:
        raise TypeError('invalid source', src)


def threading_call(target: T.Callable, *args, **kwargs):
    t = threading.Thread(target=target, args=args, kwargs=kwargs)
    t.start()


def threading_call_factory(delay: float or int = None):
    def wrapped_threading_call(target: T.Callable, *args, **kwargs):
        def wrapped_target(*_args, **_kwargs):
            if delay is not None:
                sleep(delay)
            return target(*_args, **_kwargs)

        threading_call(wrapped_target, *args, **kwargs)

    return wrapped_threading_call


class BufferedReaderChunksWrapper:
    current_chunk_size: int
    current_chunk_room: int

    def __init__(self, readable_buffer: io.BufferedReader, timeout=None, chunk_size=4096):
        if not isinstance(readable_buffer, io.BufferedReader):
            raise TypeError('readable_buffer', io.BufferedReader)
        self.buffer = readable_buffer
        self.timeout = timeout
        self.inactive = False
        self.chunks_queue = queue.Queue()
        self.chunk_memory_view = memoryview(bytearray(chunk_size))
        self.reset_current_chunk()
        if timeout is None:
            self.peek = readable_buffer.peek
            self.read = readable_buffer.read
        else:
            self.peek = ACall(readable_buffer.peek).set_timeout(timeout).get_result_timeout
            self.read = ACall(readable_buffer.read).set_timeout(timeout).get_result_timeout

    @property
    def chunk_max_size(self):
        return len(self.chunk_memory_view)

    @property
    def current_chunk_bytearray(self):
        return bytearray(self.chunk_memory_view[:self.current_chunk_size])

    def submit_current_chunk_bytearray(self):
        self.chunks_queue.put(self.current_chunk_bytearray)
        self.reset_current_chunk()

    def submit_current_chunk_bytearray_only_if_full(self):
        if self.current_chunk_size >= self.chunk_max_size:
            self.submit_current_chunk_bytearray()

    def extend_current_chunk(self, x):
        new_size = self.current_chunk_size + len(x)
        self.chunk_memory_view[self.current_chunk_size:new_size] = x
        self.current_chunk_size = new_size
        self.current_chunk_room = self.chunk_max_size - new_size

    def reset_current_chunk(self):
        self.current_chunk_size = 0
        self.current_chunk_room = self.chunk_max_size

    def scrape_to(self, dst_io):
        try:
            peek = self.peek()
            if peek:
                self.inactive = False
                data = self.read(len(peek))
                dst_io.write(data)
                dm = memoryview(data)
                dm_size = len(data)
                while self.current_chunk_room < dm_size:
                    dm_1, dm = dm[:self.current_chunk_room], dm[self.current_chunk_room:]
                    dm_size = len(dm)
                    self.extend_current_chunk(dm_1)
                    self.submit_current_chunk_bytearray()
                else:
                    self.extend_current_chunk(dm)
                    self.submit_current_chunk_bytearray_only_if_full()
            else:
                self.inactive = True
                self.submit_current_chunk_bytearray()
        except TimeoutError:
            self.inactive = True
            self.submit_current_chunk_bytearray()

    def get_chunk(self, block: bool = True, timeout: float = None):
        q = self.chunks_queue
        if q.qsize():
            return q.get(block=block, timeout=timeout)
        elif self.inactive:
            return None
        else:
            return q.get(block=block, timeout=timeout)


def get_re_groups(source: str, match_pattern=None, match_flags=None, match_method: T.Callable = re.match):
    """get_re_group_data(string[, pattern[, flags[, method]]]) -> (group(0), groups(), groupdict())"""
    args = [source]
    if match_pattern:
        args.insert(0, match_pattern)
    if match_flags:
        args.append(match_flags)
    m = match_method(*args)
    if m is None:
        return type(source)(), tuple(), dict()
    return m.group(0), m.groups(), m.groupdict()


def move_loyally___alpha(src, dst, *,
                         remove_empty_src_dir_handler=os.rmdir):
    try:
        if not os.path.exists(src):
            raise FileNotFoundError(src)
        elif os.path.isdir(src):
            if not os.path.exists(dst):
                r = patched_shutil.move(src, dst)
            elif os.path.isfile(dst):
                raise DirectoryToFileError(src, dst)
            elif os.path.isdir(dst):
                for sub in os.listdir(src):
                    patched_shutil.move(os.path.join(src, sub), dst)
                remove_empty_src_dir_handler(src)
                r = dst
            else:
                raise NeitherFileNorDirectoryError(dst)
        elif os.path.isfile(src):
            if os.path.isdir(dst):
                raise FileToDirectoryError(src, dst)
            else:
                r = patched_shutil.move(src, dst)
        else:
            raise NeitherFileNorDirectoryError(src)
        return r
    except Error as e:
        if e.args:
            msg = e.args[0]
            m = re.match(r"Destination path '(.+)' already exists", msg)
            if m:
                raise FileExistsError(m.group(1))
            else:
                raise
        else:
            raise


def move_safe___alpha(src, dst, *, error_on_exist=True, overwrite_exist=False, conflict_count=0,
                      remove_empty_src_dir_handler=os.rmdir):
    _move = functools.partial(move_loyally___alpha, remove_empty_src_dir_handler=remove_empty_src_dir_handler)
    if error_on_exist:
        if os.path.exists(dst):
            raise FileExistsError(dst)
        else:
            return _move(src, dst)

    if overwrite_exist or not os.path.exists(dst):
        return _move(src, dst)

    conflict_count += 1
    filepath_without_ext, ext = os.path.splitext(dst)
    new_dst = filepath_without_ext + f' ({conflict_count})' + ext
    if os.path.exists(new_dst):
        return move_safe___alpha(src, dst, error_on_exist=error_on_exist, overwrite_exist=overwrite_exist,
                                 conflict_count=conflict_count)
    else:
        return _move(src, new_dst)