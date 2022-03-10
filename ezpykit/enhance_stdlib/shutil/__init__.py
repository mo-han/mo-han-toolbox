#!/usr/bin/env python3
import sys
from shutil import *

from ezpykit.enhance_stdlib import os

if os.name == 'nt' and sys.version_info < (3, 8):
    import shutil as _shutil

    DEFAULT_BUFFER_SIZE = 1024 * 512


    def copyfileobj_biggerbuffer_memoryview(fsrc, fdst, length=DEFAULT_BUFFER_SIZE):
        v = memoryview(bytearray(length))
        while 1:
            n = fsrc.readinto(v)
            if not n:
                break
            elif n == length:
                fdst.write(v)
            else:
                fdst.write(v[:n])


    def copyfileobj_biggerbuffer_memoryview_threading___a(fsrc, fdst, length=DEFAULT_BUFFER_SIZE):
        """only 10% faster than `copyfileobj_biggerbuffer_memoryview`, but much more CPU usage, not worthy"""
        import threading
        import queue

        qn = 2
        q = queue.Queue(maxsize=qn)
        vl = [memoryview(bytearray(length)) for i in range(qn + 2)]  # at least 2 more than qsize,
        # so the queue's blocking can guarantee that the memoryview being written won't be altered by the read loop:
        # taken_by_write_loop <-- (the queue)[ one, another, ... ](is full) <-- new_from_read_loop(blocked)
        force_stop = threading.Event()
        rok = threading.Event()
        wok = threading.Event()
        t = 0.1

        class E:
            r = None
            w = None

        def read_loop():
            eof = False
            while 1:
                try:
                    if force_stop.is_set():
                        break
                    for v in vl:
                        n = fsrc.readinto(v)
                        # print('read')
                        if not n:
                            q.put(None)
                            eof = True
                            break
                        elif n == length:
                            q.put(v)
                        else:
                            q.put(v[:n])
                    if eof:
                        rok.set()
                        break
                except Exception as e:
                    E.r = e
            # print('reading ended')

        def write_loop():
            eof = False
            while 1:
                try:
                    if force_stop.is_set():
                        break
                    while q.qsize():
                        v = q.get()
                        if not v:
                            eof = True
                            break
                        # print('write')
                        fdst.write(v)
                    if eof:
                        wok.set()
                        break
                except Exception as e:
                    E.w = e
            # print('writing ended')

        rt = threading.Thread(target=read_loop)
        wt = threading.Thread(target=write_loop)
        rt.start()
        wt.start()

        while 1:
            try:
                if wt.is_alive():
                    wt.join(t)
                elif wok.is_set():
                    break
                elif E.w:
                    raise E.w
                else:
                    raise RuntimeError('writing interrupted', 'unknown error')
                for e in (E.r, E.w):
                    if e:
                        force_stop.set()
                        rt.join()
                        wt.join()
                        raise e
            except (KeyboardInterrupt, SystemExit):
                force_stop.set()
                rt.join()
                wt.join()
                raise
        # print('done')
        rt.join()
        wt.join()
        # print('end')


    copyfileobj = _shutil.copyfileobj = copyfileobj_biggerbuffer_memoryview


def _check_src_to_dst(src, dst):
    if os.path_isdir(dst):
        if os.path_isfile(src):
            raise Error('file to dir')
        elif os.path.isdir(src):
            return 'dir to dir'  #
        else:
            raise Error('unknown to dir')
    elif os.path_isfile(dst):
        if os.path_isfile(src):
            return 'file to file'  #
        elif os.path_isdir(src):
            raise Error('dir to file')
        else:
            raise Error('unknown to file')
    elif os.path_exists(dst):
        raise Error('unknown dst')
    else:
        if os.path_isfile(src):
            return 'new file'
        elif os.path_isdir(src):
            return 'new dir'
        else:
            return 'new unknown'


def copy_to___a(src, dst, overwrite=False, follow_symlinks=False):
    copy_to_kwargs = dict(overwrite=False, follow_symlinks=follow_symlinks)
    copy_kwargs = dict(follow_symlinks=follow_symlinks)
    copytree_kwargs = dict(symlinks=not follow_symlinks)
    r = _check_src_to_dst(src, dst)
    if r == 'dir to dir':
        if overwrite:
            raise FileExistsError(dst)
        _, sub_dirs, sub_files = next(os.walk(src))
        for d in sub_dirs:
            copy_to___a(os.join_path(src, d), os.join_path(dst, d), **copy_to_kwargs)
        for f in sub_files:
            copy2(os.join_path(src, f), dst, **copy_kwargs)
    elif r == 'file to file':
        if overwrite:
            raise FileExistsError(dst)
        copy2(src, dst, **copy_kwargs)
    elif r == 'new file':
        os.makedirs(os.get_dirname(dst), exist_ok=True)
        copy2(src, dst, **copy_kwargs)
    elif r == 'new dir':
        copytree(src, dst, **copytree_kwargs)
    else:
        raise NotImplementedError(r)


def move_to___a(src, dst, overwrite=False, follow_symlinks=False):
    move_to_kwargs = dict(overwrite=False, follow_symlinks=follow_symlinks)
    copy_kwargs = dict(follow_symlinks=follow_symlinks)
    r = _check_src_to_dst(src, dst)
    if r == 'dir to dir':
        _, sub_dirs, sub_files = next(os.walk(src))
        for d in sub_dirs:
            move_to___a(os.join_path(src, d), os.join_path(dst, d), **move_to_kwargs)
        for f in sub_files:
            fp = os.join_path(src, f)
            try:
                move(fp, dst)
            except Error as e:
                msg = e.args[0]
                if overwrite and msg.startswith('Destination path') and msg.endswith('already exists'):
                    copy2(fp, dst, **copy_kwargs)
                    os.remove(fp)
                else:
                    raise FileExistsError(os.join_path(dst, f))
    elif r == 'file to file':
        move(src, dst)
    elif r.startswith('end '):
        os.makedirs(os.get_dirname(dst), exist_ok=True)
        move(src, dst)
    else:
        raise NotImplementedError(r)


copy_to = copy_to___a
move_to = move_to___a
