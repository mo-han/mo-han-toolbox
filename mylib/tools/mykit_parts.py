#!/usr/bin/env python3
# encoding=utf8

from send2trash import send2trash

import ezpykit.stdlib.os.common
import mylib.ext.fstk
import mylib.ext.ostk
import mylib.easy
from mylib.ext import fstk, tui
from mylib.ext.ostk import clipboard
from mylib.easy import *
from mylib.easy import fstk as fstk
from mylib.easy.text import ellipt_middle

tui_lp = tui.LinePrinter()


def list_several_cloudflare_ipaddr(file, hostname, as_list, isp):
    from mylib.sites.misc import get_cloudflare_ipaddr_hostmonit
    from mylib.ext.fstk import write_json_file
    from pprint import pformat
    data = get_cloudflare_ipaddr_hostmonit()
    info: dict = data['info']
    if isp:
        info = {isp: info[isp]}
    if as_list:
        lines = []
        for ip_isp, ip_l in info.items():
            lines.append(f'# {ip_isp}')
            for ip_d in ip_l:
                li = ip_d['ip']
                if hostname:
                    li = f'{li}  {hostname}'
                lines.append(li)
        output = '\r\n'.join(lines)
    else:
        output = pformat(info)
    if file:
        write_json_file(file, data, indent=4)
    clipboard.set(output)
    print(output)


def move_into_dir(src, dst, pattern, alias, dry_run, sub_dir):
    from mylib.ext.ostk import fs_move_cli
    from ezpykit.stdlib.re import find_words
    from mylib.ext.tui import prompt_choose_number, prompt_confirm
    conf_file = fstk.make_path('~', '.config', 'fs.put_in_dir.json', user_home=True)
    conf = fstk.read_json_file(conf_file) or {'dst_map': {}}
    dst_map = conf['dst_map']
    if pattern:
        def filename_words(fn: str):
            return find_words(' '.join(re.findall(pattern, fn)))
    else:
        filename_words = find_words
    if alias is None:
        pass
    elif not alias:
        for k, v in dst_map.items():
            print(f'{k}={v}')
    else:
        for a in alias:
            try:
                k, v = a.split('=', maxsplit=1)
            except ValueError:
                k, v = None, None
            if v:
                dst_map[k] = v
                print(f'{k}={v}')
            elif k and k in dst_map:
                del dst_map[k]
                print(f'{k}=')
            else:
                print(f'{a}={dst_map.get(a, "")}')
    fstk.write_json_file(conf_file, conf, indent=4)
    if not dst:
        return
    dst = dst_map.get(dst, dst)
    sub_dirs_l = next(os.walk(dst))[1]
    __ = []
    for sub_dir_basename in sub_dirs_l:
        if re.fullmatch(r'#\w+', sub_dir_basename):
            for sub_sub_dir_basename in next(os.walk(path_join(dst, sub_dir_basename)))[1]:
                __.append(path_join(sub_dir_basename, sub_sub_dir_basename))
        else:
            __.append(sub_dir_basename)
    sub_dirs_l = __
    if os.path.isfile(dst):
        print(f'! {dst} is file (should be directory)', file=sys.stderr)
        exit(1)
    os.makedirs(dst, exist_ok=True)
    db_path = fstk.make_path(dst, '__folder_name_words__.db')
    db = mylib.ext.fstk.read_sqlite_dict_file(db_path)
    db = {k: v for k, v in db.items() if k in sub_dirs_l}
    sub_dirs_d = {sd_bn: set(find_words(sd_bn.lower())) for sd_bn in sub_dirs_l if sd_bn not in db}
    # sd_bn: sub-dir basename
    sub_dirs_d.update(db)
    sub_dirs_d = {k: sub_dirs_d[k] for k in sorted(sub_dirs_d)}
    for ss in src:
        for s in fstk.path_or_glob(ss):
            tui_lp.d()
            print(s)
            tui_lp.l()
            if sub_dir:
                similar_d = {basename: words_set & set(filename_words(os.path.basename(s).lower()))
                             for basename, words_set in sub_dirs_d.items()}
                similar_d = {k: v for k, v in similar_d.items() if v}
                similar_l = sorted(similar_d, key=lambda x: similar_d[x], reverse=True)
                if similar_l:
                    target_dir_name = prompt_choose_number(f'Select probable folder:', similar_l)
                    tui_lp.l()
                else:
                    target_dir_name = None
                if not target_dir_name:
                    keywords = input('Input custom keywords or leave it empty: ')
                    if keywords:
                        similar_d = {basename: words_set & set(filename_words(keywords.lower()))
                                     for basename, words_set in sub_dirs_d.items()}
                        similar_d = {k: v for k, v in similar_d.items() if v}
                        similar_l = sorted(similar_d, key=lambda x: similar_d[x], reverse=True)
                        if similar_l:
                            target_dir_name = prompt_choose_number(f'Select probable folder for\n{keywords}:',
                                                                   similar_l)
                            tui_lp.l()
                target_dir_name = target_dir_name or input(f'Create folder: ')
                if target_dir_name:
                    sub_dirs_d[target_dir_name] = set(find_words(target_dir_name.lower()))
                    dir_path = fstk.make_path(dst, target_dir_name)
                    if not dry_run:
                        os.makedirs(dir_path, exist_ok=True)
                else:
                    dir_path = dst
            else:
                dir_path = dst
            d = fstk.make_path(dir_path, os.path.basename(s))
            if os.path.exists(d):
                if not prompt_confirm(f'Overwrite {d}?', default=False):
                    continue
            if not dry_run:
                fs_move_cli(s, d)
            print(f'{s} -> {d}')
    mylib.ext.fstk.write_sqlite_dict_file(db_path, sub_dirs_d, update_only=True)


def flat_dir(src, prefix, dry_run):
    is_win32 = os.name == 'nt'
    for s in src:
        if not os.path.isdir(s):
            print(f'! skip non-folder: {s}')
            continue
        with ezpykit.stdlib.os.common.ctx_pushd(s):
            print(s)
            for fp in fstk.find_iter('f', '.', win32_unc=is_win32):
                new = os.path.relpath(fp, fstk.make_path('.', win32_unc=is_win32))
                if not prefix:
                    new = os.path.basename(new)
                new = ellipt_middle(fstk.sanitize(new), 250, encoding='utf8')
                print(new)
                if not dry_run:
                    shutil.move(fp, fstk.make_path(new, win32_unc=is_win32))
            if dry_run:
                return
            for dp in fstk.find_iter('d', '.', include_start_dir=False, win32_unc=is_win32):
                try:
                    os.removedirs(dp)
                except OSError:
                    for p, d, f in os.walk(dp):
                        if f:
                            send2trash(dp)
                            break
