#!/usr/bin/env python3
import os
import sys

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
        """about 10% speed-up compared with `copyfileobj_biggerbuffer_memoryview`, still cannot handle ctrl-c"""
        import threading
        import queue

        qn = 2
        q = queue.Queue(maxsize=qn)
        vl = [memoryview(bytearray(length)) for i in range(qn)]
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


    copyfileobj = _shutil.copyfileobj = copyfileobj_biggerbuffer_memoryview_threading___a
    copyfile = _shutil.copyfile
    copy = _shutil.copy
    copy2 = _shutil.copy2
    copytree = _shutil.copytree
    move = _shutil.move
