#!/usr/bin/env python3
# encoding=utf8
import argparse
import os
from time import time
from zipfile import ZipFile, BadZipFile
import shutil
from mylib.os_auto import clipboard as cb
from mylib.tricks_lite import thread_factory
from mylib.os_auto import list_files
from queue import Queue
from threading import Thread

ap = argparse.ArgumentParser()
ap.add_argument('-s', '--src', nargs='*')
ap.add_argument('-d', '--dest-dir')
ap.add_argument('-r', '--recursive')
args = ap.parse_args()

src = args.src
dest = args.dest_dir
recursive = args.recursive

print(f'-> {dest}')
q = Queue()


def progress():
    w = shutil.get_terminal_size()[0] - 1
    m = (w - 5) // 4
    t0 = time()
    while True:
        p = q.get()
        if p is None:
            break
        ps = f'{" " * w}\r{p[:m]} ... {p[-m:]}'
        t1 = time()
        if t1 - t0 > 0.2:
            print(ps, end='\r')
            t0 = t1


t = thread_factory(daemon=True)(progress)
t.run()
files_l = list_files(src or cb, recursive=recursive, progress_queue=q)
x, y, z = 0, 0, 0
print()
for fp in files_l:
    z += 1
    try:
        zf = ZipFile(fp)
    except BadZipFile:
        continue
    y += 1
    for f in zf.namelist():
        if f.endswith('.webp'):
            break
    else:
        zf.close()
        dfp = os.path.join(dest, os.path.split(fp)[-1])
        shutil.move(fp, dfp)
        x += 1
        print(f'* {fp}')
    print(f'| {x} | {y} | {z} |', end='\r')
