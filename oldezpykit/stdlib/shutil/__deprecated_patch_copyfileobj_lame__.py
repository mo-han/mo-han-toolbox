#!/usr/bin/env python3
import shutil as patched_shutil
from shutil import *

from oldezpykit.allinone import *

COPY_BUFFER_SIZE = 16 * 1024 * 1024


def shutil_copy_file_obj_fast_with_larger_default_buffer_size(
        src_fd, dst_fd,
        length: int = COPY_BUFFER_SIZE
):
    return copyfileobj(src_fd, dst_fd, length)


def shutil_copy_file_obj_faster_with_parallel_read_write_thread___devel_stage(src_fd, dst_fd, length: int = None):
    length = length or COPY_BUFFER_SIZE
    q_max = 2
    q = queue.Queue(maxsize=q_max)
    d = {'e': None, 't': 0.0, 'E': None}
    stop = threading.Event()

    def read_loop():
        while 1:
            if stop.is_set():
                break
            if q.qsize() == q_max:
                sleep(d['t'])
                continue
            t0 = time.perf_counter()
            try:
                buf = src_fd.read(length)
            except Exception as e:
                d['e'] = e
            else:
                if buf:
                    q.put(buf)
                else:
                    q.put(None)
                    break
            d['t'] = time.perf_counter() - t0
        # print(read_loop.__name__, 'stopped')

    def write_loop():
        while 1:
            if stop.is_set():
                break
            buf = q.get()
            if buf is None:
                break
            else:
                dst_fd.write(buf)
        # print(write_loop.__name__, 'stopped')

    t_read = threading.Thread(target=read_loop)
    t_write = threading.Thread(target=write_loop)
    t_read.start()
    t_write.start()

    while 1:
        try:
            if t_write.is_alive():
                t_write.join(d['t'])
            else:
                break
            if d['e']:
                stop.set()
                d['E'] = d['e']
                break
        except (KeyboardInterrupt, SystemExit) as e:
            stop.set()
            d['E'] = e
            break
    error = d['E']
    if error:
        t_write.join()
        t_read.join()
        # print('raise', repr(error))
        raise error


# patched_shutil.copyfileobj = shutil_copy_file_obj_faster_with_parallel_read_write_thread___devel_stage
patched_shutil.copyfileobj = shutil_copy_file_obj_fast_with_larger_default_buffer_size
copy = patched_shutil.copy
copy2 = patched_shutil.copy2
copytree = patched_shutil.copytree
move = patched_shutil.move
