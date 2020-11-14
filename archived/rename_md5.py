#!/usr/bin/env python
"""Rename file(s) to MD5 with original file extension."""

from glob import glob
from hashlib import md5
from os import rename
from os.path import splitext, split, join
from sys import argv

if __name__ == '__main__':
    for a in argv[1:]:
        print('+ {}:'.format(a))
        al = glob(a.replace('[', '[[]'))
        if not al:
            al = [a]
        for f in al:
            with open(f, 'rb') as fd:
                h = md5(fd.read()).hexdigest()
            pd, bn = split(f)
            _, x = splitext(bn)
            n = join(pd, h + x)
            print('  + {} -> {}'.format(f, n))
            rename(f, n)
