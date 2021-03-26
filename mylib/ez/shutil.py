#!/usr/bin/env python3
import shutil as shutil_

from .often import *

global_config = {'copy.buffer.size': 16 * 1024 * 1024}


def _shutil_move_safe(src, dst, *, error_on_exist=True, overwrite_exist=False, conflict_count=0):
    if error_on_exist:
        if os.path.exists(dst):
            raise FileExistsError(dst)
        else:
            return shutil_.move(src, dst)

    if overwrite_exist:
        return shutil_.move(src, dst)

    if not os.path.exists(dst):
        return shutil_.move(src, dst)

    conflict_count += 1
    trunk, ext = os.path.splitext(dst)
    new_trunk = trunk + f' ({conflict_count})'
    new_dst = new_trunk + ext
    if os.path.exists(new_dst):
        return _shutil_move_safe(src, dst, error_on_exist=error_on_exist, overwrite_exist=overwrite_exist,
                                 conflict_count=conflict_count)
    else:
        return shutil_.move(src, new_dst)


shutil_.move_safe = _shutil_move_safe


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
    data_array = [0.0]

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
            data_array[0] = td
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
                t_write.join(data_array[0])
            else:
                break
    except (KeyboardInterrupt, SystemExit):
        stop.set()
        raise


shutil_.copyfileobj = shutil_copy_file_obj_faster
