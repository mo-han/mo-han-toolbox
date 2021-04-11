#!/usr/bin/env python3
import functools
import shutil as patched_shutil
from shutil import *

from .__often_used_imports__ import *

global_config = {'copy.buffer.size': 16 * 1024 * 1024}


def __refer_sth():
    return copyfileobj


def shutil_copy_file_obj_fast(src_fd, dst_fd, length: int = None):
    length = length or global_config['copy.buffer.size']
    while 1:
        buf = src_fd.read(length)
        if not buf:
            break
        dst_fd.write(buf)


def shutil_copy_file_obj_faster(src_fd, dst_fd, length: int = None):
    length = length or global_config['copy.buffer.size']
    q_max = 2
    q = queue.Queue(maxsize=q_max)
    stop = threading.Event()
    registers = [0.0]

    def read():
        t0 = time.perf_counter()
        while 1:
            if stop.isSet():
                break
            t1 = time.perf_counter()
            td = t1 - t0
            t0 = t1
            if q.qsize() == q_max:
                sleep(td)
                continue
            buf = src_fd.read(length)
            if buf:
                q.put(buf)
            else:
                q.put(None)
                break

    def write():
        t0 = time.perf_counter()
        while 1:
            if stop.isSet():
                break
            t1 = time.perf_counter()
            td = t1 - t0
            registers[0] = td
            t0 = t1
            try:
                buf = q.get()
            except queue.Empty:
                sleep(td)
                continue
            if buf is None:
                break
            else:
                dst_fd.write(buf)

    t_read = threading.Thread(target=read)
    t_write = threading.Thread(target=write)
    t_read.start()
    t_write.start()
    try:
        while 1:
            if t_write.is_alive():
                t_write.join(registers[0])
            else:
                break
    except (KeyboardInterrupt, SystemExit):
        stop.set()
        raise


patched_shutil.copyfileobj = shutil_copy_file_obj_faster
copy = patched_shutil.copy
copy2 = patched_shutil.copy2


class FilesystemOperationError(Exception):
    pass


class FileToDirectoryError(FilesystemOperationError):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class DirectoryToFileError(FilesystemOperationError):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class NeitherFileNorDirectoryError(FilesystemOperationError):
    pass


def dir_is_empty(dirname):
    if not os.path.isdir(dirname):
        raise NotADirectoryError(dirname)
    return not bool(os.listdir(dirname))


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
