#!/usr/bin/env python
"""Rename file(s) to MD5 with original file extension."""

from os import rename
from os.path import splitext
from sys import argv
from hashlib import md5

if __name__ == '__main__':
    f = argv[1]
    d = open(f, 'rb')
    h = md5(d.read()).hexdigest()
    d.close()
    _, x = splitext(f)
    n = h+x
    print(f, '->', n)
    rename(f, n)
