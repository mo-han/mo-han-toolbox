#!/usr/bin/env python3
import fnmatch

from mylib.ext import fstk
from mylib.ext.console_app import *
from mylib.easy import logging

_logger = logging.ez_get_logger(__name__)

FILE_DIR_CHOICES = {'f', 'd', 'fd'}
ON_EXIST_CHOICES = {'error', 'overwrite', 'rename'}

apr = ArgumentParserRigger()
an = apr.an
path_is_file = os.path.isfile
path_is_dir = os.path.isdir
an.s = an.src = an.PATH = an.dst = an.D = an.in_dst = an.S = an.in_src = an.v = an.verbose = an.F = an.conflict = ''
an.x = an.exclude = an.dry_run = an.R = an.recurse = an.p = an.pattern = an.r = an.replace = an.t = an.filter_type = ''


def main():
    apr.parse()
    apr.run()


class FilesystemError(OSError):
    pass


@apr.sub(apr.rnu(), help='remove sub-dirs, put sub-files in flat structure', aliases=['flat.dir'])
def flatten_dir():
    ...


@apr.sub(help='move multiple src to/into dst')
@apr.arg(an.dst)
@apr.opt(an.s, an.src, nargs='*', metavar=an.PATH)
@apr.true(an.D, apr.make_option_name_from_dest_name(an.in_dst))
@apr.true(an.S, apr.make_option_name_from_dest_name(an.in_src))
@apr.opt(an.F, an.conflict, choices=ON_EXIST_CHOICES, default='error')
@apr.opt(an.x, an.exclude)
@apr.true(an.v, an.verbose)
@apr.true(long_name=apr.make_option_name_from_dest_name(an.dry_run))
@apr.map(an.dst, an.src, in_dst=an.in_dst, in_src=an.in_src, conflict=an.conflict, exclude=an.exclude,
         verbose=an.verbose, dry_run=an.dry_run)
def mv2(dst: str, src: T.Union[T.List[str], str, T.NoneType] = None, *, in_dst: bool = False, in_src: bool = False,
        conflict: ON_EXIST_CHOICES = 'error', exclude=None, verbose: bool = False, dry_run: bool = False):
    get_basename = os.path.basename

    on_exist = fstk.OnExist(value=conflict)
    dirs, files = resolve_path_to_dirs_files(src)
    src_l = dirs + files
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
        raise FilesystemError('one dst path for many src')

    for one_src in src_l:
        if in_src and os.path.isdir(one_src):
            one_src_expand = [fstk.make_path(one_src, bn) for bn in os.listdir(one_src)]
        else:
            one_src_expand = [one_src]
        for a_src in one_src_expand:
            the_src_bn = get_basename(a_src)
            if exclude and fnmatch.fnmatch(the_src_bn, exclude):
                continue
            the_dst = fstk.make_path(dst, the_src_bn) if in_dst_dir else dst
            moved_dst = fstk.move_as(a_src, the_dst, on_exist=on_exist, dry_run=dry_run, predicate_path_use_cache=False)
            if verbose:
                print(f'"{moved_dst}" <- "{a_src}"')


if __name__ == '__main__':
    main()
