#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re


def jijidown_rename_alpha(path: str, part_num=True):
    rename = os.rename
    isfile = os.path.isfile
    isdir = os.path.isdir
    basename = os.path.basename
    dirname = os.path.dirname
    path_join = os.path.join

    def _ren_file(filepath):
        name = basename(filepath)
        parent = dirname(filepath)
        print('{}:'.format(parent))
        new_name = re.sub(r'\.[Ff]lv\.mp4$', '.mp4', name)
        new_name = re.sub(r'^(\d+\.)?(.*?)\(Av(\d+).*?\)', r'\1 \2 [av\3]', new_name)
        if not part_num:
            new_name = re.sub(r'^\d+\.', '', new_name)
        if new_name[-5:] == '].ass' and new_name[-8:-5] != '+弹幕':
            new_name = new_name[:-5] + '+弹幕].ass'
        elif new_name[-5:] == '].xml' and new_name[-8:-5] != '+弹幕':
            new_name = new_name[:-5] +  '+弹幕].xml'
        elif new_name[-6:] == 'lv.mp4':
            new_name = new_name[:-8] + '.mp4'
        print('{} -> {}'.format(name, new_name))
        new_filepath = path_join(parent, new_name)
        rename(filepath, new_filepath)

    if isfile(path):
        _ren_file(path)
    elif isdir(path):
        for i in [path_join(path, f) for f in os.listdir(path)]: _ren_file(i)
    else:
        print('Not exist: {}'.format(path))
