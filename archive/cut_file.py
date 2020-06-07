#!/usr/bin/env python

import sys


def _cut_file_bytes(file: str, size: int) -> bytes:
    if size == 0:
        return b''
    with open(file, 'rb') as f:
        if size > 0:
            return f.read()[0:size]
        else:
            return f.read()[size:]


if __name__ == '__main__':
    fp = sys.argv[1]
    s = sys.argv[2]
    with open('cutfile.tmp', 'wb') as cf:
        cf.write(_cut_file_bytes(fp, int(s)))
