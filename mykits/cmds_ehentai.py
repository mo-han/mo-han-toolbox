#!/usr/bin/env python3
from mylib.ex.console_app import *
from mylib.sites import ehentai

apr = ArgumentParserRigger()
an = apr.an


def _sorted_path_of_hentai_at_home_downloaded_gallery(gallery_path, gallery_type=''):
    _unknown_ = '(unknown)'
    _various_ = '(various)'

    info = ehentai.parse_hentai_at_home_downloaded_gallery_info(gallery_path, gallery_type)
    if not info:
        return None
    title = info['title']
    sanitized_title = fstk.sanitize_xu240(title)
    artist = info['tags']['artist']
    group = info['tags']['group']
    root_dir, name, ext = split_path_dir_base_ext(gallery_path, dir_ext=False)

    creators = artist or group or []
    if len(creators) > 3:
        creators_s = _various_
    else:
        creators_s = ', '.join(creators) or _unknown_

    new_root = fstk.make_path(root_dir, creators_s)
    dst: str = join_path_dir_base_ext(new_root, f'{sanitized_title} {info["gid_resize"]}', ext)
    return dst


an.src = an.v = an.verbose = an.D = an.dry_run = ''


@apr.sub(apr.replace_underscore())
@apr.arg(an.src, nargs='*')
@apr.true(an.v, an.verbose)
@apr.true(an.D, apr.fmt_opt(an.dry_run))
@apr.map(an.src, verbose=an.verbose, dry_run=an.dry_run)
def hath_sort(src: PathSourceType, *, verbose=False, dry_run=False):
    """rename and sort galleries download via H@H (Hentai at Home)"""
    dirs, files = resolve_path_to_dirs_files(src)
    src_dst_l = []
    [src_dst_l.append((src, _sorted_path_of_hentai_at_home_downloaded_gallery(src, 'd'))) for src in dirs]
    [src_dst_l.append((src, _sorted_path_of_hentai_at_home_downloaded_gallery(src, 'f'))) for src in files]
    for src, dst in src_dst_l:
        if not dst and verbose:
            print(f'# {src}')
        try:
            if not dry_run:
                fstk.move_as(src, dst)
                if verbose:
                    print(f'* {dst} <- {src}')
        except Exception as e:
            if verbose:
                print(f'! {src}: {repr(e)}')
