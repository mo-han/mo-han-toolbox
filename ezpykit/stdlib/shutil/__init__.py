#!/usr/bin/env python3
import sys
from shutil import *

from ezpykit.stdlib import os

if os.name == 'nt' and sys.version_info < (3, 8):
    import shutil as _shutil
    from ezpykit.stdlib.shutil.patch_fastercopy import copyfileobj_biggerbuffer_memoryview

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
