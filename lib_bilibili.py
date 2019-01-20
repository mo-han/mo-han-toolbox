#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from glob import glob


def jijidown_rename_alpha(path: str):
    rename = os.rename
    isfile = os.path.isfile
    isdir = os.path.isdir
    cd = os.chdir
    basename = os.path.basename
    dirname = os.path.dirname
    path_join = os.path.join

    def _ren_file(filepath):
        name = basename(filepath)
        parent = dirname(filepath)
        new_name = re.sub(r'\.[Ff]lv\.mp4$', '.mp4', name)
        new_name = re.sub(r'^(\d+\.)?(.*?)\(Av(\d+).*?\)', r'\1 \2 [av\3]', new_name)
        new_filepath = path_join(parent, new_name)
        rename(filepath, new_filepath)

    if isfile(path):
        _ren_file(path)
    elif isdir(path):
        for f in glob(path_join(path, '*')): _ren_file(f)
    else:
        print('Not exist: {}'.format(path))
