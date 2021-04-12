#!/usr/bin/env python3
from mylib.ex import ostk
from mylib.ex import fstk
from mylib.ez import *
from mylib.ez import argparse
from mylib.ez import logging
from fnmatch import fnmatch

_logger = logging.get_logger(__name__)

apr = argparse.ArgumentParserRigger()
an = apr.an


class FilesystemError(OSError):
    pass


an.s = an.src = an.dst = an.D = an.in_dst = an.S = an.in_src = an.v = an.verbose = an.F = an.conflict = None
an.x = an.exclude = None


@apr.sub()
@apr.arg(an.dst)
@apr.opt(an.s, an.src, nargs='*')
@apr.true(an.D, apr.make_option_name(an.in_dst))
@apr.true(an.S, apr.make_option_name(an.in_src))
@apr.opt(an.F, an.conflict, choices=['error', 'overwrite', 'rename'], default='error')
@apr.opt(an.x, an.exclude)
@apr.true(an.v, an.verbose)
@apr.map(an.dst, an.src, in_dst=an.in_dst, in_src=an.in_src, conflict=an.conflict, exclude=an.exclude,
         verbose=an.verbose)
def move(dst: str, src: T.Union[T.List[str]] = None, *, in_dst: bool = False, in_src: bool = False,
         conflict='error' or 'overwrite' or 'rename', exclude=None, verbose: bool = False):
    get_basename = os.path.basename

    on_exist_ = fstk.OnExist
    on_exist = {'error': on_exist_.ERROR, 'overwrite': on_exist_.OVERWRITE, 'rename': on_exist_.RENAME}[conflict]
    if not src:
        src_l = ostk.clipboard.list_path()
    else:
        src_l = []
        for s in src:
            s_glob = glob.glob(s)
            if s_glob == [s]:
                src_l.append(s)
            else:
                src_l.extend(s_glob)
    if not src_l:
        return
    dst_is_dir = os.path.isdir(dst)
    in_dst_dir = dst_is_dir and in_dst
    if in_dst and not dst_is_dir:
        raise NotADirectoryError(dst)

    src_is_many = len(src_l) > 1
    cnt = 0
    if in_src:
        for s in src_l:
            if os.path.isfile(s):
                cnt += 1
            if os.path.isdir(s):
                dirname, sub_dirs, sub_files = next(os.walk(s))
                cnt += len(sub_dirs) + len(sub_files)
            if cnt > 1:
                src_is_many = True
                break
    if src_is_many and not in_dst_dir:
        raise FilesystemError('one dst path for many dst')

    for one_src in src_l:
        one_src_l = [fstk.make_path(one_src, sub) for sub in os.listdir(one_src)] if in_src and os.path.isdir(one_src) \
            else [one_src]
        for the_src in one_src_l:
            the_src_bn = get_basename(the_src)
            if exclude and fnmatch(the_src_bn, exclude):
                continue
            the_dst = fstk.make_path(dst, the_src_bn) if in_dst_dir else dst
            fstk.move(the_src, the_dst, on_exist=on_exist)
            if verbose:
                print(f'{the_src} <- {the_dst}')


def main():
    if len(sys.argv) < 2:
        sys.argv.append('-h')
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
