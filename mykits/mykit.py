#!/usr/bin/env python3
# encoding=utf8
"""This tool heavily depends on `mylib` package, make sure `mylib` folder is in the same path with this tool."""

import cmd
import shlex
from argparse import ArgumentParser, REMAINDER
from collections import defaultdict
from pprint import pprint

from send2trash import send2trash

import mylib.__deprecated__
import mylib.easy
import mylib.ext.ostk
from ezpykit import AttrName
from mylib.__deprecated__ import fs_inplace_rename, fs_inplace_rename_regex, list_files, list_dirs
from mylib.cli import arg_type_pow2, arg_type_range_factory, add_dry_run
from mylib.easy import *
from ezpykit.stdlib.argparse import CompactHelpFormatterWithDefaults
from mylib.ext.tricks import Attreebute, eval_or_str, deco_factory_exit_on_keyboard_interrupt
from mylib.ext import fstk, tui
from mylib.ext.fstk import make_path, ctx_pushd
from mylib.ext.ostk import clipboard, set_console_title

rtd = Attreebute()  # runtime data
tui_lp = tui.LinePrinter()
an = AttrName()
common_parser_kwargs = {'formatter_class': CompactHelpFormatterWithDefaults}
ap = ArgumentParser(**common_parser_kwargs)
sub = ap.add_subparsers(title='sub-commands')


class HasParser:
    parser: ArgumentParser

    @classmethod
    def run(cls):
        pass


def has_parser_done(cls: HasParser):
    cls.parser.set_defaults(target=cls.run)
    return cls


class MyKitCmd(cmd.Cmd):
    last_not_repeat = None

    def __init__(self):
        super(MyKitCmd, self).__init__()
        self.prompt = __class__.__name__ + ':\n'
        self._stop = None
        self._done = None

    def precmd(self, line):
        if line:
            tui_lp.l(shorter=1)
        self._done = False
        return line

    def postcmd(self, stop, line):
        if self._done:
            tui_lp.l(shorter=1)
        return self._stop

    def emptyline(self):
        return

    def default(self, line):
        try:
            argv_l = shlex.split(line)
            rtd.args = args = ap.parse_args(argv_l)
            func = args.target
            if func not in [cmd_mode_func, gui_mode]:
                self._done = func
                return func()
            else:
                self._done = None
        except SystemExit:
            pass

    def do_quit(self, line):
        self._stop = True

    do_exit = do_q = do_quit

    def do_repeat(self, line):
        if self.last_not_repeat:
            return self.onecmd(self.last_not_repeat)

    do_r = do_repeat

    def onecmd(self, line):
        super(MyKitCmd, self).onecmd(line)
        if self.lastcmd not in ('r', 'repeat'):
            self.last_not_repeat = self.lastcmd


def main():
    # from mylib.os_util import ensure_sigint_signal
    # ensure_sigint_signal()
    rtd.args = args = ap.parse_args()
    try:
        target = args.target
    except AttributeError:
        target = cmd_mode_func
    target()


def add_sub_parser(name: str, aliases: list = None, desc: str = None, target=None) -> ArgumentParser:
    aliases = aliases or []
    sub_parser = sub.add_parser(name, aliases=aliases, help=desc, description=desc, **common_parser_kwargs)
    if target:
        sub_parser.set_defaults(target=target)
    return sub_parser


def test_only():
    print('ok')


test = add_sub_parser('test', [], 'for testing...')
test.set_defaults(target=test_only)


def gui_mode():
    pass


def cmd_mode_func():
    set_console_title(MyKitCmd.__name__)
    MyKitCmd().cmdloop()


cmd_mode = add_sub_parser('cmd', ['cli'], 'command line interactive mode')
cmd_mode.set_defaults(target=cmd_mode_func)


def merge_zip_files_func():
    from more_itertools import all_equal
    from fs import open_fs
    from fs.compress import write_zip
    from fs.copy import copy_fs_if_newer
    from filetype import guess

    def ask_for_dst_path():
        return tui.prompt_input('? Input the path of the ZIP file to merge into: ')

    def is_zip_file(path: str):
        mime = guess(path).mime
        if mime == 'application/zip':
            return True
        else:
            print('! Not a ZIP file: {path}')
            return False

    args = rtd.args
    dry_run = args.dry_run
    auto_yes = args.yes
    src_l = args.src or mylib.ext.ostk.clipboard.list_path()
    src_l = [s for s in src_l if is_zip_file(s)]

    if len(src_l) < 2:
        print(f'! at least 2 zip files')
        return
    print('# Merge all below ZIP files:')
    print('\n'.join(src_l))
    dbx_l = [mylib.easy.split_path_dir_base_ext(p) for p in src_l]
    if all_equal([d for d, b, x in dbx_l]):
        common_dir = dbx_l[0][0]
    else:
        common_dir = ''
    if all_equal([x for d, b, x in dbx_l]):
        common_ext = dbx_l[0][-1]
    else:
        common_ext = ''
    if common_dir and common_ext:
        common_base = os.path.commonprefix([b for d, b, x in dbx_l]).strip()
        if common_base:
            tmp_dst = mylib.easy.join_path_dir_base_ext(common_dir, common_base, common_ext)
            if auto_yes or tui.prompt_confirm(f'? Merge into ZIP file "{tmp_dst}"', default=True):
                dst = tmp_dst
            else:
                dst = ask_for_dst_path()
        else:
            dst = ask_for_dst_path()
    elif common_dir:
        if auto_yes or tui.prompt_confirm(f'? Put merged ZIP file into this dir "{common_dir}"', default=True):
            filename = tui.prompt_input(f'? Input the basename of the ZIP file to merge into: ')
            dst = fstk.make_path(common_dir, filename)
        else:
            dst = ask_for_dst_path()
    else:
        dst = ask_for_dst_path()
    if dry_run:
        print(f'@ Merge into ZIP file "{dst}"')
        return
    print(f'* Merge into ZIP file "{dst}"')
    with open_fs('mem://tmp') as tmp:
        for s in src_l:
            with open_fs(f'zip://{s}') as z:
                copy_fs_if_newer(z, tmp)  # todo: seem check time of ZIP-FS but not files inside
        write_zip(tmp, dst)
    for s in src_l:
        if s == dst:
            continue
        send2trash(s)
        print(f'# Trash <- {s}')


merge_zip_files = add_sub_parser('merge.zip.files', ['mg.zip'], 'merge multiple files', merge_zip_files_func)
add_dry_run(merge_zip_files)
merge_zip_files.add_argument('src', nargs='*')
merge_zip_files.add_argument('-y', '--yes', help='auto confirm yes', action='store_true')


def tag_filter_files_func():
    from mylib.easy.filename_tags import EnclosedFilenameTagsSet
    args = rtd.args
    ext_rm = set(args.X or [])
    ext_kp = set(args.x or [])
    tag_rm = set(args.T or [])
    tag_kp = set(args.t or [])
    dry = args.dry_run
    rm = defaultdict(set)
    kp = defaultdict(set)
    for f in fstk.files_from_iter(args.src or mylib.ext.ostk.clipboard.list_path(), recursive=False):
        ft = EnclosedFilenameTagsSet(f)
        ext = ft.extension
        prefix = ft.before_tags
        if any(map(ft.has_tag, tag_kp)) or ext in ext_kp:
            kp[prefix].add(f)
        elif any(map(ft.has_tag, tag_rm)) or ext in ext_rm:
            rm[prefix].add(f)
        else:
            kp[prefix].add(f)
    for prefix, rm_set in rm.items():
        kp_set = kp.get(prefix, set())
        if kp_set:
            print(f'@ {prefix}')
            for f in kp_set:
                print(f'# {f}')
            for f in rm_set - kp_set:
                print(f'- {f}')
                if not dry:
                    try:
                        send2trash(f)
                    except OSError:
                        shutil.remove(f)


tag_filter_files = add_sub_parser('tag.filter.files', [], 'filter files by tags and ext')
tag_ff = tag_filter_files
tag_ff.set_defaults(target=tag_filter_files_func)
tag_ff.add_argument('src', nargs='*')
tag_ff.add_argument('-D', '--dry-run', action='store_true')
tag_ff.add_argument('-X', dest='X', metavar='ext', nargs='*', help='files with these extensions will be removed')
tag_ff.add_argument('-x', dest='x', metavar='ext', nargs='*', help='files with these extensions will be kept')
tag_ff.add_argument('-T', dest='T', metavar='tag', nargs='*', help='files with these tags will be removed')
tag_ff.add_argument('-t', dest='t', metavar='tag', nargs='*', help='files with these tags will be kept')


def catalog_files_by_year_func():
    import shutil
    args = rtd.args
    suffix_l = args.suffix or ['']
    dry_run = args.dry_run
    files = (p for p in fstk.files_from_iter(args.src or mylib.ext.ostk.clipboard.list_path()) if
             any(map(p.endswith, suffix_l)))
    for f in files:
        dirname, basename = os.path.split(f)
        year = re.findall(r'(\d{4})-\d{2}-\d{2}', basename)
        if not year:
            continue
        year = year[0]
        new_dir = make_path(dirname, year)
        print(f'{new_dir} <- {basename}')
        if not dry_run:
            with ctx_pushd(new_dir, ensure_dst=True):
                shutil.move(f, basename)


catalog_files_by_year = add_sub_parser('catalog.files.year', ['clf.yr'],
                                       'catalog files into sub-folders by year (search ISO 8601 date in filename)')
catalog_files_by_year.set_defaults(target=catalog_files_by_year_func)
catalog_files_by_year.add_argument('-x', '--suffix', metavar='ext', nargs='*')
catalog_files_by_year.add_argument('-D', '--dry-run', action='store_true')
catalog_files_by_year.add_argument('src', nargs='*')


@has_parser_done
class GetCloudflareIP(HasParser):
    parser = add_sub_parser('cfip', [], 'get cloudflare ip addresses from hostmonit.com')
    parser.add_argument('file', help='write whole data to JSON file', nargs='?')
    parser.add_argument('-L', '--list', action='store_true')
    parser.add_argument('-P', '--isp', choices=('CM', 'CT', 'CU'))
    parser.add_argument('-H', '--hostname')

    @classmethod
    def run(cls):
        from mylib.tools.mykit_parts import list_several_cloudflare_ipaddr
        args = rtd.args
        file = args.file
        as_list = args.list
        isp = args.isp
        hostname = args.hostname
        list_several_cloudflare_ipaddr(file, hostname, as_list, isp)


def video_guess_crf_func():
    from mylib.ffmpeg_alpha import guess_video_crf, file_is_video
    args = rtd.args
    path_l = [path for path in list_files(args.src or clipboard) if file_is_video(path)]
    codec = args.codec
    work_dir = args.work_dir
    redo = args.redo
    auto_clean = not args.no_clean
    for path in path_l:
        tui_lp.l()
        tui_lp.p(path)
        try:
            tui_lp.p(guess_video_crf(src=path, codec=codec, work_dir=work_dir, redo=redo, auto_clean=auto_clean))
        except (KeyError, ZeroDivisionError) as e:
            tui_lp.p(f'! {repr(e)}')
            tui_lp.p(f'- {path}')


video_guess_crf = add_sub_parser('video.crf.guess', ['crf'], 'guess CRF parameter value of video file')
video_guess_crf.set_defaults(target=video_guess_crf_func)
video_guess_crf.add_argument('src', nargs='*')
video_guess_crf.add_argument('-c', '--codec', nargs='?')
video_guess_crf.add_argument('-w', '--work-dir')
video_guess_crf.add_argument('-R', '--redo', action='store_true')
video_guess_crf.add_argument('-L', '--no-clean', action='store_true')


@has_parser_done
class FlatDir(HasParser):
    parser = add_sub_parser('flatten-directory', ['flat-dir'])
    parser.add_argument('-p', f'--prefix', action='store_true')
    parser.add_argument('-D', '--dry-run', action='store_true')
    parser.add_argument('src', nargs='*')

    @classmethod
    def run(cls):
        from mylib.tools.mykit_parts import flat_dir
        args = rtd.args
        prefix = args.prefix
        dry_run = args.dry_run
        src = args.src or mylib.ext.ostk.clipboard.list_path()
        # print(prefix, dry_run, src)
        flat_dir(src, prefix, dry_run)


@has_parser_done
class MoveIntoDir(HasParser):
    parser = add_sub_parser('move-into-directory', ['mvd'])
    parser.add_argument('-D', '--dry-run', action='store_true')
    parser.add_argument('-a', '--alias', nargs='*', help='list, show, set or delete dst mapping aliases')
    parser.add_argument('-d', '--sub-dir', action='store_true', help='into sub-directory by name')
    parser.add_argument('-p', '--pattern')
    parser.add_argument('dst', nargs='?', help='dest dir')
    parser.add_argument('src', nargs='*')

    @classmethod
    @deco_factory_exit_on_keyboard_interrupt(2)
    def run(cls):
        from mylib.tools.mykit_parts import move_into_dir
        args = rtd.args
        src = args.src or mylib.ext.ostk.clipboard.list_path()
        dst = args.dst
        alias = args.alias
        dry_run = args.dry_run
        sub_dir = args.sub_dir
        pattern = args.pattern
        move_into_dir(src, dst, pattern, alias, dry_run, sub_dir)


def tail_filter_files_func():
    from mylib.ext.ostk import filter_filename_tail, join_filename_tail
    args = rtd.args
    tk = set(args.tails_keep or [])
    xk = set(args.extensions_keep or [])
    tg = set(args.tails_gone or [])
    xg = set(args.extensions_gone or [])
    dry = args.dry_run
    src = list_files(args.src or clipboard, recursive=False)
    from collections import defaultdict
    keep = defaultdict(list)
    gone = defaultdict(list)
    for dn, fn, tail, ext in filter_filename_tail(src, tk | tg, tk, xk):
        keep[(dn, fn)].append((tail, ext))
    for dn, fn, tail, ext in filter_filename_tail(src, tk | tg, tg, xg):
        gone[(dn, fn)].append((tail, ext))
    for g in gone:
        if g in keep:
            dn, fn = g
            tui_lp.l()
            print(f'* {os.path.join(dn, fn)}')
            for tail, ext in keep[g]:
                print(f'@ {tail} {ext}')
            for tail, ext in gone[g]:
                print(f'- {tail} {ext}')
                if not dry:
                    send2trash(join_filename_tail(dn, fn, tail, ext))


tail_filter_files = add_sub_parser('tail.filter.files', [], 'filter files by filename tails and extensions')
tail_ff = tail_filter_files
tail_ff.set_defaults(target=tail_filter_files_func)
tail_ff.add_argument('-t', '--tails-keep', nargs='*', metavar='tail', help='keep files with these tails')
tail_ff.add_argument('-x', '--extensions-keep', nargs='*', metavar='ext', help='keep files with these extensions')
tail_ff.add_argument('-T', '--tails-gone', nargs='*', metavar='tail', help='remove files with these tails')
tail_ff.add_argument('-X', '--extensions-gone', nargs='*', metavar='ext', help='remove files with these extensions')
tail_ff.add_argument('-D', '--dry-run', action='store_true')
tail_ff.add_argument('src', nargs='*')


def cookies_write_func():
    import json
    from mylib.web_client import convert_cookies_json_to_netscape
    args = rtd.args
    files = args.file or list_files(clipboard, recursive=False)
    verbose = args.verbose
    for fp in files:
        tui_lp.l()
        print(f'* {fp}')
        data = input('# input cookies data, or copy data to clipboard and press enter:\n')
        if not data:
            print(f'# empty input, paste from clipboard')
            data = clipboard.get()
        if verbose:
            pprint(data)
        try:
            j = json.loads(data)
            c = convert_cookies_json_to_netscape(j, disable_filepath=True)
        except json.decoder.JSONDecodeError:
            c = data
        if verbose:
            pprint(c)
        with open(fp, 'w') as f:
            f.write(c)


cookies_write = add_sub_parser('cookies.write', ['cwr'], 'write cookies file')
cookies_write.set_defaults(target=cookies_write_func)
cookies_write.add_argument('file', nargs='*')
cookies_write.add_argument('-v', '--verbose', action='store_true')


def ccj_func():
    from mylib.web_client import convert_cookies_file_json_to_netscape
    files = rtd.args.file or list_files(clipboard, recursive=False)
    for fp in files:
        print(f'* {fp}')
        convert_cookies_file_json_to_netscape(fp)


cookies_conv_json = add_sub_parser('cookies.conv.json', ['ccj'], 'convert .json cookies file')
cookies_conv_json.set_defaults(target=ccj_func)
cookies_conv_json.add_argument('file', nargs='*')


def ffmpeg_img2vid_func():
    from mylib.ffmpeg_alpha import FFmpegRunnerAlpha, FFmpegArgsList, parse_kw_opt_str
    ff = FFmpegRunnerAlpha(banner=False, overwrite=True)
    ff.logger.setLevel('INFO')
    args = rtd.args
    images = args.images
    output = args.output or f'{os.path.split(os.path.abspath(images))[0]}.mp4'
    res_fps = args.res_fps
    keywords = args.keyword or ()
    ffmpeg_options = args.opt or ()
    output_args = FFmpegArgsList()
    if os.path.isdir(os.path.dirname(images)):
        images_l = [images]
    else:
        images_l = [os.path.join(folder, images) for folder in mylib.ext.ostk.clipboard.list_path() if
                    os.path.isdir(folder)]
    for i in images_l:
        if output in ('mp4', 'webm'):
            o = f'{os.path.realpath(os.path.dirname(i))}.{output}'
        else:
            o = output
        for kw in keywords:
            output_args.add(*parse_kw_opt_str(kw))
        output_args.add(*ffmpeg_options)
        try:
            tui_lp.l()
            print(i)
            print(o)
            ff.img2vid(i, res_fps, o, output_args)
        except KeyboardInterrupt:
            exit(2)


ffmpeg_img2vid = add_sub_parser('ffmpeg.img2vid', ['img2vid'], 'convert images (frames) into video using ffmpeg')
ffmpeg_img2vid.set_defaults(target=ffmpeg_img2vid_func)
ffmpeg_img2vid.add_argument('-i', '--images', help='input images, e.g. "%%03d.jpg"', required=True)
ffmpeg_img2vid.add_argument('-o', '--output', help='output video', nargs='?')
ffmpeg_img2vid.add_argument('-r', '--res-fps', metavar='WxH@FPS', required=True)
ffmpeg_img2vid.add_argument('-k', '--keyword', nargs='*', help='')
ffmpeg_img2vid.add_argument('opt', help='ffmpeg options (better insert -- before them)', nargs='*')


def ffmpeg_func():
    from mylib.ffmpeg_alpha import kw_video_convert
    args = rtd.args
    source = args.source or clipboard
    keywords = args.keywords or ()
    video_filters = args.video_filters
    cut_points = args.cut_points
    output_path = args.output_path
    overwrite = args.overwrite
    redo_origin = args.redo_origin
    verbose = args.verbose
    dry_run = args.dry_run
    opts = args.opts
    if verbose:
        print(args)
    for filepath in mylib.__deprecated__.list_files(source, recursive=False):
        kw_video_convert(filepath, keywords=keywords, vf=video_filters, cut_points=cut_points, dest=output_path,
                         overwrite=overwrite, redo=redo_origin, verbose=verbose, dry_run=dry_run, ffmpeg_opts=opts)


ffmpeg = add_sub_parser('wrap.ffmpeg', ['ffmpeg', 'ff'], 'convert video file using ffmpeg')
ffmpeg.set_defaults(target=ffmpeg_func)
ffmpeg.add_argument('-s', '--source', nargs='*', metavar='path', help='if omitted, will try paths in clipboard')
ffmpeg.add_argument('-k', '--keywords', metavar='kw', nargs='*')
ffmpeg.add_argument('-vf', '--video-filters', nargs='*')
ffmpeg.add_argument('-t', '--time-cut', dest='cut_points', metavar='ts', nargs='*')
ffmpeg.add_argument('-o', '--output-path')
ffmpeg.add_argument('-O', '--overwrite', action='store_true')
ffmpeg.add_argument('-R', '--redo-origin', action='store_true')
ffmpeg.add_argument('-v', '--verbose', action='count', default=0)
ffmpeg.add_argument('-D', '--dry-run', action='store_true')
ffmpeg.add_argument('opts', nargs='*', help='ffmpeg options (insert -- before opts)')


def ffprobe_func():
    from ffmpeg import probe
    from pprint import pprint
    file = rtd.args.file
    ss = rtd.args.select_streams
    if not file:
        file = mylib.ext.ostk.clipboard.list_path()[0]
    if ss:
        pprint(probe(file, select_streams=ss))
    else:
        pprint(probe(file))


ffprobe = add_sub_parser('wrap.ffprobe', ['ffprobe', 'ffp'], 'json format ffprobe on a file')
ffprobe.set_defaults(target=ffprobe_func)
ffprobe.add_argument('-s', '--select-streams')
ffprobe.add_argument('file', nargs='?')


def file_type_func():
    from filetype import guess
    files = rtd.args.file
    if rtd.args.print_no_path:
        fmt = '{type}'
    else:
        fmt = '{type} ({file})'
    if not files:
        files = mylib.ext.ostk.clipboard.list_path()(exist_only=True)
    for f in files:
        try:
            print(fmt.format(type=guess(f).mime, file=f))
        except AttributeError:
            print('N/A')


file_type = add_sub_parser('filetype', ['ftype', 'ft'], 'get file type by path')
file_type.set_defaults(target=file_type_func)
file_type.add_argument('file', nargs='*')
file_type.add_argument('-P', '--print-no-path', action='store_true')


def pip2pi_func():
    from mylib.pip2pi_x import libpip2pi_commands_x
    import sys
    argv0 = ' '.join(sys.argv[:2]) + ' --'
    sys.argv = [argv0] + rtd.args.arg
    libpip2pi_commands_x.pip2pi(['pip2pi'] + rtd.args.arg)


pip2pi = add_sub_parser('pip2pi', [], 'modified pip2pi (from pip2pi)')
pip2pi.set_defaults(target=pip2pi_func)
pip2pi.add_argument('arg', nargs='*', help='arguments propagated to pip2pi, put a -- before them')


def dir2pi_func():
    from mylib.pip2pi_x import libpip2pi_commands_x
    import sys
    argv0 = ' '.join(sys.argv[:2]) + ' --'
    sys.argv = [argv0] + rtd.args.arg
    libpip2pi_commands_x.dir2pi(['dir2pi'] + rtd.args.arg)


dir2pi = add_sub_parser('dir2pi', [], 'modified dir2pi (from pip2pi)')
dir2pi.set_defaults(target=dir2pi_func)
dir2pi.add_argument('arg', nargs='*', help='arguments propagated to dir2pi, put a -- before them')


def ytdl_func():
    from mylib.youtube_dl_x import youtube_dl_main_x
    import sys
    argv0 = ' '.join(sys.argv[:2]) + ' --'
    sys.argv = [argv0] + rtd.args.param
    youtube_dl_main_x()


ytdl = add_sub_parser('ytdl', [], 'youtube-dl with modifications: [iwara.tv] fix missing uploader')
ytdl.set_defaults(target=ytdl_func)
ytdl.add_argument('param', nargs='*', help='argument(s) propagated to youtube-dl, better put a -- before it')


def regex_rename_func():
    args = rtd.args
    source = args.source
    recursive = args.recursive
    pattern = args.pattern
    replace = args.replace
    only_basename = args.only_basename
    dry_run = args.dry_run
    only_dirs = args.only_dirs
    if only_dirs:
        src_l = list_dirs(source or clipboard, recursive=recursive)
    else:
        src_l = list_files(source or clipboard, recursive=recursive)
    for src in src_l:
        try:
            fs_inplace_rename_regex(src, pattern, replace, only_basename, dry_run)
        except OSError as e:
            print(repr(e))


regex_rename = add_sub_parser('rename.regex', ['regren', 'rern', 'rrn'], 'regex rename file(s) or folder(s)')
regex_rename.set_defaults(target=regex_rename_func)
regex_rename.add_argument('-B', '-not-only-basename', dest='only_basename', action='store_false')
regex_rename.add_argument('-D', '--dry-run', action='store_true')
regex_rename.add_argument('-d', '--only-dirs', action='store_true')
regex_rename.add_argument('-s', '--source')
regex_rename.add_argument('-r', '--recursive', action='store_true')
regex_rename.add_argument('pattern')
regex_rename.add_argument('replace')


def rename_func():
    args = rtd.args
    source = args.source
    recursive = args.recursive
    pattern = args.pattern
    replace = args.replace
    only_basename = args.only_basename
    dry_run = args.dry_run
    only_dirs = args.only_dirs
    if only_dirs:
        src_l = list_dirs(source or clipboard, recursive=recursive)
    else:
        src_l = list_files(source or clipboard, recursive=recursive)
    # print(source)
    # print(src_l)
    for src in src_l:
        try:
            fs_inplace_rename(src, pattern, replace, only_basename, dry_run)
        except OSError as e:
            print(repr(e))


rename = add_sub_parser('rename', ['ren'], 'rename file(s) or folder(s)')
rename.set_defaults(target=rename_func)
rename.add_argument('-B', '-not-only-basename', dest='only_basename', action='store_false')
rename.add_argument('-D', '--dry-run', action='store_true')
rename.add_argument('-d', '--only-dirs', action='store_true')
rename.add_argument('-s', '--source')
rename.add_argument('-r', '--recursive', action='store_true')
rename.add_argument('pattern')
rename.add_argument('replace')


def run_from_lines_func():
    import os
    args = rtd.args
    source = args.source
    dry_run = args.dry_run
    cmd_fmt = ' '.join(args.command) or input('< ')
    if '{}' in cmd_fmt:
        cmd_fmt = cmd_fmt.replace('{}', '{line}')
    if '{line}' not in cmd_fmt:
        cmd_fmt += ' "{line}"'
    print('>', cmd_fmt, file=sys.stderr)
    if source == ':clipboard.path':
        lines = mylib.ext.ostk.clipboard.list_path()
    elif source == ':clipboard':
        lines = str(clipboard.get()).splitlines()
    elif source:
        with open(source, 'r') as fd:
            lines = fd.readlines()
    else:
        lines = []
    try:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            command = cmd_fmt.format(line=line.strip())
            print('#', command, file=sys.stderr)
            if not dry_run:
                os.system(command)
    except KeyboardInterrupt:
        sys.exit(2)


run_from_lines = add_sub_parser(
    'run.from.lines', ['run.lines', 'rl'],
    'given lines from file, clipboard, etc. formatted command will be executed for each of the line')
run_from_lines.set_defaults(target=run_from_lines_func)
run_from_lines.add_argument('-s', '--source', help='":clipboard", ":clipboard.path", or path of file (text lines)')
run_from_lines.add_argument('command', nargs='*')
run_from_lines.add_argument('-D', '--dry-run', action='store_true')


def dukto_x_func():
    from mylib.dukto import run, copy_recv_text, config_at
    from threading import Thread
    from queue import Queue
    args = rtd.args
    config_at.server.text.queue = Queue()
    config_at.server.msg_echo = args.echo
    t = Thread(target=copy_recv_text, args=(args.file, args.clipboard))
    t.daemon = True
    ndrop_args = rtd.args.ndrop_args
    while ndrop_args and ndrop_args[0] == '--':
        ndrop_args.pop(0)
    sys.argv[0] = 'mykit dukto-x'
    sys.argv[1:] = ndrop_args
    t.start()
    run()


dukto_x = add_sub_parser('dukto-x', ['dukto'],
                         'extended dukto server, remainder arguments conform to ndrop')
dukto_x.set_defaults(target=dukto_x_func)
dukto_x.add_argument('-f', '--copy-text-to-file', metavar='file', dest='file')
dukto_x.add_argument('-c', '--copy-text-to-clipboard', action='store_true', dest='clipboard')
dukto_x.add_argument('-e', '--echo', action='store_true')
dukto_x.add_argument('ndrop_args', metavar='[--] arguments for ndrop', nargs=REMAINDER)


def url_from_clipboard():
    from expykit import os
    from mylib.easy.text import regex_find
    from html import unescape
    args = rtd.args
    pattern = args.pattern
    try:
        t = os.clipboard.get_html()
    except (AttributeError, TypeError):
        t = os.clipboard.get()
    if not pattern:
        urls = []
    elif pattern == 'ed2k':
        p = r'ed2k://[^/]+/'
        urls = regex_find(p, t, dedup=True)
    elif pattern == 'magnet':
        p = r'magnet:[^\s"]+'
        urls = regex_find(p, unescape(t), dedup=True)
    elif pattern == 'iwara':
        from mylib.sites.iwara import find_video_url
        urls = find_video_url(t)
    elif pattern in ('pornhub', 'ph'):
        from mylib.sites.pornhub import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern in ('youtube', 'ytb'):
        from mylib.sites.youtube import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern in ('bilibili', 'bili'):
        from mylib.sites.bilibili.__to_be_deprecated__ import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern in ('hc.fyi', 'hentai.cafe', 'hentaicafe'):
        p = r'https://hentai.cafe/hc.fyi/\d+'
        urls = regex_find(p, t, dedup=True)
    else:
        urls = regex_find(pattern, t, dedup=True)
    urls = '\r\n'.join(urls)
    os.clipboard.clear()
    os.clipboard.set(urls)
    print(urls)


clipboard_findurl = add_sub_parser('clipboard.findurl', ['cb.url', 'cburl'],
                                   'find URLs from clipboard, then copy found URLs back to clipboard')
clipboard_findurl.set_defaults(target=url_from_clipboard)
clipboard_findurl.add_argument('pattern', help='URL pattern, or website name')


def clipboard_rename_func():
    from mylib.gui_old import rename_dialog
    for f in mylib.ext.ostk.clipboard.list_path():
        rename_dialog(f)


clipboard_rename = add_sub_parser('clipboard.rename', ['cb.ren', 'cbren'], 'rename files in clipboard')
clipboard_rename.set_defaults(target=clipboard_rename_func)


def potplayer_rename_func():
    from mylib.enchant.potplayer import PotPlayerKit
    args = rtd.args
    PotPlayerKit().rename_file_gui(alt_tab=args.no_keep_front)


potplayer_rename = add_sub_parser('potplayer.rename', ['pp.ren', 'ppren'], 'rename media file opened in PotPlayer')
potplayer_rename.set_defaults(target=potplayer_rename_func)
potplayer_rename.add_argument('-F', '--no-keep-front', action='store_true', help='do not keep PotPlayer in front')


def bilibili_download_func():
    from mylib.sites.bilibili.__to_be_deprecated__ import download_bilibili_video
    args = rtd.args
    if args.verbose:
        print(args)
    download_bilibili_video(**vars(args))


bilibili_download = add_sub_parser('bilibili.download', ['bldl'], 'bilibili video downloader (source-patched you-get)')
bilibili_download.set_defaults(target=bilibili_download_func)
bilibili_download.add_argument('url')
bilibili_download.add_argument('-v', '--verbose', action='store_true')
bilibili_download.add_argument('-f', '--force', action='store_true')
bilibili_download.add_argument('-c', '--cookies', metavar='FILE')
bilibili_download.add_argument('-i', '--info', action='store_true')
bilibili_download.add_argument('-l', '--playlist', action='store_true', help='BUGGY! DO NOT USE!')
bilibili_download.add_argument('-o', '--output', metavar='dir')
bilibili_download.add_argument('-p', '--parts', nargs='*', metavar='N')
bilibili_download.add_argument('-q', '--qn-want', type=int, metavar='N',
                               help='120, 116, 112, 80, 74, 64, 48, 32, 16, 0')
bilibili_download.add_argument('-Q', '--qn-max', type=int, metavar='N', default=116,
                               help='max qn (quality number), default to 116 (1080P60), not 120 (4K).')
bilibili_download.add_argument('-C', '--no-caption', dest='caption', action='store_false')
bilibili_download.add_argument('-A', '--no-moderate-audio', dest='moderate_audio', action='store_false',
                               help='by default the best quality audio is NOT used, '
                                    'instead, a moderate quality (~128kbps) is chose, which is good enough. '
                                    'this option force choosing the best quality audio stream')


def json_edit_func():
    from mylib.ext.fstk import write_json_file
    from mylib.ext.fstk import read_json_file
    args = rtd.args
    file = args.file or list_files(clipboard)[0]
    indent = args.indent
    delete = args.delete
    item_l = args.item
    d = read_json_file(file)

    if delete:
        def handle(key, value):
            if key in d:
                if value:
                    if d[key] == value:
                        del d[key]
                else:
                    del d[key]
    else:
        def handle(key, value):
            d[key] = value

    for item in item_l:
        k, v = map(eval_or_str, item.split('=', maxsplit=1))
        handle(k, v)
    write_json_file(file, d, indent=indent)


json_edit = add_sub_parser('json.edit', ['jse'], 'edit JSON file')
json_edit.set_defaults(target=json_edit_func)
json_edit.add_argument('-f', '--file', nargs='?')
json_edit.add_argument('-i', '--indent', type=int, default=4)
json_edit.add_argument('-d', '--delete', action='store_true')
json_edit.add_argument('item', nargs='+')


def json_key_func():
    from mylib.ext.fstk import read_json_file
    args = rtd.args
    d = read_json_file(args.file)
    print(d[args.key])


json_key = add_sub_parser('json.getkey', ['jsk'], 'find in JSON file by key')
json_key.set_defaults(target=json_key_func)
json_key.add_argument('file', help='JSON file to query')
json_key.add_argument('key', help='query key')


def update_json_file():
    from mylib.ext.fstk import write_json_file
    from mylib.ext.fstk import read_json_file
    args = rtd.args
    old, new = args.old, args.new
    d = read_json_file(old)
    d.update(read_json_file(new))
    write_json_file(old, d, indent=args.indent)


json_update = add_sub_parser('json.update', ['jsup'], 'update <old> JSON file with <new>')
json_update.set_defaults(target=update_json_file)
json_update.add_argument('old', help='JSON file with old data')
json_update.add_argument('new', help='JSON file with new data')
json_update.add_argument('-t', '--indent', type=int, default=4, metavar='N')


def view_similar_images():
    from mylib.picture import view_similar_images_auto
    args = rtd.args
    kwargs = {
        'thresholds': args.thresholds,
        'hashtype': args.hashtype,
        'hashsize': args.hashsize,
        'trans': args.transpose,
        'dryrun': args.dry_run,
    }
    dir_l = (p for p in (args.dir or mylib.ext.ostk.clipboard.list_path()) if os.path.isdir(p))
    if dir_l:
        for d in dir_l:
            with ctx_pushd(d):
                view_similar_images_auto(**kwargs)
    else:
        view_similar_images_auto(**kwargs)


img_sim_view = add_sub_parser('img.sim.view', ['vsi'], 'view similar images in current working directory')
img_sim_view.set_defaults(target=view_similar_images)
img_sim_view.add_argument('dir', nargs='*')
img_sim_view.add_argument(
    '-t', '--thresholds', type=arg_type_range_factory(float, '0<x<=1'), nargs='+', metavar='N',
    help='(multiple) similarity thresholds')
img_sim_view.add_argument(
    '-H', '--hashtype', type=str, choices=[s + 'hash' for s in ('a', 'd', 'p', 'w')], help='image hash type')
img_sim_view.add_argument(
    '-s', '--hashsize', type=arg_type_pow2, metavar='N',
    help='the side size of the image hash square, must be a integer power of 2')
img_sim_view.add_argument(
    '-T', '--no-transpose', action='store_false', dest='transpose',
    help='do not find similar images for transposed variants (rotated, flipped)')
img_sim_view.add_argument(
    '-D', '--dry-run', action='store_true', help='find similar images, but without viewing them')


def move_ehviewer_images():
    from mylib.sites.ehentai import ehviewer_images_catalog
    args = rtd.args
    ehviewer_images_catalog(args.src or mylib.ext.ostk.clipboard.list_path()[0],
                            dry_run=args.dry_run, db_json_path=args.db_json or 'ehdb.json')


ehv_img_mv = add_sub_parser('ehv.img.mv', ['ehvmv'],
                            'move ehviewer downloaded images into folders')
ehv_img_mv.set_defaults(target=move_ehviewer_images)
ehv_img_mv.add_argument('-D', '--dry-run', action='store_true')
ehv_img_mv.add_argument('-j', '--db-json')
ehv_img_mv.add_argument('-s', '--src', nargs='?')

if __name__ == '__main__':
    main()
