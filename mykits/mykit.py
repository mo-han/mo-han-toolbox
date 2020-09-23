#!/usr/bin/env python3
# encoding=utf8
"""This tool heavily depends on `mylib` package, make sure `mylib` folder is in the same path with this tool."""

import cmd
import os
import shlex
import sys
from argparse import ArgumentParser, REMAINDER

from send2trash import send2trash

from mylib.tui import LinePrinter
from mylib.os_util import clipboard, list_files
from mylib.tricks import arg_type_pow2, arg_type_range_factory, ArgParseCompactHelpFormatter, Attreebute

rtd = Attreebute()  # runtime data
cli_draw = LinePrinter()
common_parser_kwargs = {'formatter_class': ArgParseCompactHelpFormatter}
ap = ArgumentParser(**common_parser_kwargs)
sub = ap.add_subparsers(title='sub-commands')


class MyKitCmd(cmd.Cmd):
    last_not_repeat = None

    def __init__(self):
        super(MyKitCmd, self).__init__()
        self.prompt = __class__.__name__ + ':\n'
        self._stop = None
        self._done = None

    def precmd(self, line):
        if line:
            cli_draw.l(shorter=1)
        self._done = False
        return line

    def postcmd(self, stop, line):
        if self._done:
            cli_draw.l(shorter=1)
        return self._stop

    def emptyline(self):
        return

    def default(self, line):
        try:
            argv_l = shlex.split(line)
            rtd.args = args = ap.parse_args(argv_l)
            func = args.func
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
        func = args.func
    except AttributeError:
        func = cmd_mode_func
    func()


def add_sub_parser(name: str, aliases: list, desc: str) -> ArgumentParser:
    return sub.add_parser(name, aliases=aliases, help=desc, description=desc, **common_parser_kwargs)


def test_only():
    print('ok')


test = add_sub_parser('test', [], 'for testing...')
test.set_defaults(func=test_only)


def gui_mode():
    pass


def cmd_mode_func():
    MyKitCmd().cmdloop()


cmd_mode = add_sub_parser('cmd', ['cli'], 'command line interactive mode')
cmd_mode.set_defaults(func=cmd_mode_func)


def clear_redundant_files_func():
    from mylib.os_util import filter_filename_tail, join_filename_tail
    lp = LinePrinter()
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
            lp.l()
            print(f'* {os.path.join(dn, fn)}')
            for tail, ext in keep[g]:
                print(f'@ {tail} {ext}')
            for tail, ext in gone[g]:
                print(f'- {tail} {ext}')
                if not dry:
                    send2trash(join_filename_tail(dn, fn, tail, ext))


files_clear_redundant = add_sub_parser('file.clear.redundant', ['fcr', 'crf'], 'clear files with related names')
fcr = files_clear_redundant
fcr.set_defaults(func=clear_redundant_files_func)
fcr.add_argument('-t', '--tails-keep', nargs='*', metavar='tail', help='keep files with these tails')
fcr.add_argument('-x', '--extensions-keep', nargs='*', metavar='ext', help='keep files with these extensions')
fcr.add_argument('-T', '--tails-gone', nargs='*', metavar='tail', help='remove files with these tails')
fcr.add_argument('-X', '--extensions-gone', nargs='*', metavar='ext', help='remove files with these extensions')
fcr.add_argument('-D', '--dry-run', action='store_true')
fcr.add_argument('src', nargs='*')


def ccj_func():
    from mylib.web_client import convert_cookies_file_json_to_netscape
    files = rtd.args.file or list_files(clipboard, recursive=False)
    for fp in files:
        print(f'* {fp}')
        convert_cookies_file_json_to_netscape(fp)


ccj = add_sub_parser('cookies.conv.json', ['ccj'], 'convert .json cookies file')
ccj.set_defaults(func=ccj_func)
ccj.add_argument('file', nargs='*')


def vid_mhc_func():
    from mylib.ffmpeg_local import mark_high_crf_video_file
    args = rtd.args
    threshold = args.crf_threshold
    codec = args.codec
    res_limit = args.resolution_limit
    clean = not args.no_clean
    work_dir = args.work_dir
    redo_origin = args.redo_origin
    src = args.src or clipboard
    mark_high_crf_video_file(src=src, crf_thres=threshold, codec=codec, res_limit=res_limit,
                             redo=redo_origin, work_dir=work_dir, auto_clean=clean)


vid_mhc = add_sub_parser('video.mark.high.crf', ['vmhc'],
                         'mark video file with high crf (estimated), '
                         'by appending ".origin" in its filename (before file extension)')
vid_mhc.set_defaults(func=vid_mhc_func)
vid_mhc.add_argument('-t', '--crf-threshold', type=float, default=22)
vid_mhc.add_argument('-c', '--codec', choices=('a', 'h'))
vid_mhc.add_argument('-m', '--resolution-limit', choices=('FHD', 'HD'))
vid_mhc.add_argument('-L', '--no-clean', action='store_true', help='not clean temp files in work dir')
vid_mhc.add_argument('-W', '--work-dir')
vid_mhc.add_argument('-R', '--redo', action='store_true', dest='redo_origin')
vid_mhc.add_argument('src', nargs='*')


def ffmpeg_func():
    from mylib.ffmpeg_local import kw_video_convert
    args = rtd.args
    source = args.source or clipboard
    keywords = args.keywords or ()
    cut_points = args.cut_points
    output_path = args.output_path
    overwrite = args.overwrite
    redo_origin = args.redo_origin
    verbose = args.verbose
    opts = args.opts
    if verbose:
        print(args)
    kw_video_convert(source=source, keywords=keywords, cut_points=cut_points, dest=output_path,
                     overwrite=overwrite, redo=redo_origin, verbose=verbose, ffmpeg_opts=opts)


ffmpeg = add_sub_parser('wrap.ffmpeg', ['ffmpeg', 'ff'], 'convert video file using ffmpeg')
ffmpeg.set_defaults(func=ffmpeg_func)
ffmpeg.add_argument('-s', '--source', nargs='*', metavar='path', help='if omitted, will try paths in clipboard')
ffmpeg.add_argument('-k', '--keywords', metavar='kw', nargs='*')
ffmpeg.add_argument('-t', '--time-cut', dest='cut_points', metavar='ts', nargs='*')
ffmpeg.add_argument('-o', '--output-path')
ffmpeg.add_argument('-O', '--overwrite', action='store_true')
ffmpeg.add_argument('-R', '--redo-origin', action='store_true')
ffmpeg.add_argument('-v', '--verbose', action='count', default=0)
ffmpeg.add_argument('opts', nargs='*', help='ffmpeg options (insert -- before opts)')


def ffprobe_func():
    from ffmpeg import probe
    from pprint import pprint
    file = rtd.args.file
    ss = rtd.args.select_streams
    if not file:
        file = clipboard.list_paths()[0]
    if ss:
        pprint(probe(file, select_streams=ss))
    else:
        pprint(probe(file))


ffprobe = add_sub_parser('wrap.ffprobe', ['ffprobe', 'ffp'], 'json format ffprobe on a file')
ffprobe.set_defaults(func=ffprobe_func)
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
        files = clipboard.list_paths(exist_only=True)
    for f in files:
        try:
            print(fmt.format(type=guess(f).mime, file=f))
        except AttributeError:
            print('N/A')


file_type = add_sub_parser('filetype', ['ftype', 'ft'], 'get file type by path')
file_type.set_defaults(func=file_type_func)
file_type.add_argument('file', nargs='*')
file_type.add_argument('-P', '--print-no-path', action='store_true')


def pip2pi_func():
    from mylib.pip2pi_x import libpip2pi_commands_x
    import sys
    argv0 = ' '.join(sys.argv[:2]) + ' --'
    sys.argv = [argv0] + rtd.args.arg
    libpip2pi_commands_x.pip2pi(['pip2pi'] + rtd.args.arg)


pip2pi = add_sub_parser('pip2pi', [], 'modified pip2pi (from pip2pi)')
pip2pi.set_defaults(func=pip2pi_func)
pip2pi.add_argument('arg', nargs='*', help='arguments propagated to pip2pi, put a -- before them')


def dir2pi_func():
    from mylib.pip2pi_x import libpip2pi_commands_x
    import sys
    argv0 = ' '.join(sys.argv[:2]) + ' --'
    sys.argv = [argv0] + rtd.args.arg
    libpip2pi_commands_x.dir2pi(['dir2pi'] + rtd.args.arg)


dir2pi = add_sub_parser('dir2pi', [], 'modified dir2pi (from pip2pi)')
dir2pi.set_defaults(func=dir2pi_func)
dir2pi.add_argument('arg', nargs='*', help='arguments propagated to dir2pi, put a -- before them')


def ytdl_func():
    from mylib.ytdl import youtube_dl_main_x
    import sys
    argv0 = ' '.join(sys.argv[:2]) + ' --'
    sys.argv = [argv0] + rtd.args.argv
    youtube_dl_main_x()


ytdl = add_sub_parser('ytdl', [], 'youtube-dl with modifications: [iwara.tv] fix missing uploader')
ytdl.set_defaults(func=ytdl_func)
ytdl.add_argument('argv', nargs='*', help='argument(s) propagated to youtube-dl, better put a -- before it')


def regex_rename_func():
    from mylib.os_util import fs_inplace_rename_regex, list_files
    args = rtd.args
    source = args.source
    recursive = args.recursive
    pattern = args.pattern
    replace = args.replace
    only_basename = args.only_basename
    dry_run = args.dry_run
    for src in list_files(source or clipboard, recursive=recursive):
        try:
            fs_inplace_rename_regex(src, pattern, replace, only_basename, dry_run)
        except OSError as e:
            print(repr(e))


regex_rename = add_sub_parser('rename.regex', ['regren', 'rern', 'rrn'], 'regex rename file(s) or folder(s)')
regex_rename.set_defaults(func=regex_rename_func)
regex_rename.add_argument('-B', '-not-only-basename', dest='only_basename', action='store_false')
regex_rename.add_argument('-D', '--dry-run', action='store_true')
regex_rename.add_argument('-s', '--source')
regex_rename.add_argument('-r', '--recursive', action='store_true')
regex_rename.add_argument('pattern')
regex_rename.add_argument('replace')


def rename_func():
    from mylib.os_util import fs_inplace_rename, list_files
    args = rtd.args
    source = args.source
    recursive = args.recursive
    pattern = args.pattern
    replace = args.replace
    only_basename = args.only_basename
    dry_run = args.dry_run
    for src in list_files(source or clipboard, recursive=recursive):
        try:
            fs_inplace_rename(src, pattern, replace, only_basename, dry_run)
        except OSError as e:
            print(repr(e))


rename = add_sub_parser('rename', ['ren'], 'rename file(s) or folder(s)')
rename.set_defaults(func=regex_rename_func)
rename.add_argument('-B', '-not-only-basename', dest='only_basename', action='store_false')
rename.add_argument('-D', '--dry-run', action='store_true')
rename.add_argument('-s', '--source')
rename.add_argument('-r', '--recursive', action='store_true')
rename.add_argument('pattern')
rename.add_argument('replace')


def run_from_lines_func():
    import os
    args = rtd.args
    file = args.file
    dry_run = args.dry_run
    cmd_fmt = ' '.join(args.command) or input('< ')
    if '{}' not in cmd_fmt:
        cmd_fmt += ' {}'
    print('>', cmd_fmt)
    if file:
        with open(file, 'r') as fd:
            lines = fd.readlines()
    else:
        lines = str(clipboard.get()).splitlines()
    try:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            command = cmd_fmt.format(line.strip())
            print('#', command)
            if not dry_run:
                os.system(command)
    except KeyboardInterrupt:
        sys.exit(2)


run_from_lines = add_sub_parser(
    'run.from.lines', ['runlines', 'rl'],
    'given lines from file, clipboard, etc. formatted command will be executed for each of the line')
run_from_lines.set_defaults(func=run_from_lines_func)
run_from_lines.add_argument('-f', '--file', help='text file of lines')
run_from_lines.add_argument('command', nargs='*', help='format command from this string and a line')
run_from_lines.add_argument('-D', '--dry-run', action='store_true')


def dukto_x_func():
    from mylib.dukto import run, copy_recv_text, config_at
    from threading import Thread
    from queue import Queue
    args = rtd.args
    config_at.server.text.queue = Queue()
    config_at.server.echo = args.echo
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
dukto_x.set_defaults(func=dukto_x_func)
dukto_x.add_argument('-f', '--copy-text-to-file', metavar='file', dest='file')
dukto_x.add_argument('-c', '--copy-text-to-clipboard', action='store_true', dest='clipboard')
dukto_x.add_argument('-e', '--echo', action='store_true')
dukto_x.add_argument('ndrop_args', metavar='[--] arguments for ndrop', nargs=REMAINDER)


def url_from_clipboard():
    import pyperclip
    from mylib.text import regex_find
    from mylib.web_client import decode_html_char_ref
    args = rtd.args
    pattern = args.pattern
    t = pyperclip.paste()
    if pattern == 'ed2k':
        p = r'ed2k://[^/]+/'
        urls = regex_find(p, t, dedup=True)
    elif pattern == 'magnet':
        p = r'magnet:[^\s"]+'
        urls = regex_find(p, decode_html_char_ref(t), dedup=True)
    elif pattern == 'iwara':
        from mylib.iwara import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern in ('pornhub', 'ph'):
        from mylib.pornhub import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern in ('youtube', 'ytb'):
        from mylib.youtube import find_url_in_text
        urls = find_url_in_text(t)
    else:
        from mylib.text import regex_find
        urls = regex_find(pattern, t)
    urls = '\n'.join(urls)
    pyperclip.copy(urls)
    print(urls)


clipboard_findurl = add_sub_parser('clipboard.findurl', ['cb.url', 'cburl'],
                                   'find URLs from clipboard, then copy found URLs back to clipboard')
clipboard_findurl.set_defaults(func=url_from_clipboard)
clipboard_findurl.add_argument('pattern', help='URL pattern, or website name')


def clipboard_rename_func():
    from mylib.gui import rename_dialog
    for f in clipboard.list_paths():
        rename_dialog(f)


clipboard_rename = add_sub_parser('clipboard.rename', ['cb.ren', 'cbren'], 'rename files in clipboard')
clipboard_rename.set_defaults(func=clipboard_rename_func)


def potplayer_rename_func():
    from mylib.potplayer import PotPlayerKit
    args = rtd.args
    PotPlayerKit().rename_file_gui(alt_tab=args.no_keep_front)


potplayer_rename = add_sub_parser('potplayer.rename', ['pp.ren', 'ppren'], 'rename media file opened in PotPlayer')
potplayer_rename.set_defaults(func=potplayer_rename_func)
potplayer_rename.add_argument('-F', '--no-keep-front', action='store_true', help='do not keep PotPlayer in front')


def bilibili_download_func():
    from mylib.bilibili import download_bilibili_video
    args = rtd.args
    if args.verbose:
        print(args)
    download_bilibili_video(**vars(args))


bilibili_download = add_sub_parser('bilibili.download', ['bldl'], 'bilibili video downloader (source-patched you-get)')
bilibili_download.set_defaults(func=bilibili_download_func)
bilibili_download.add_argument('url')
bilibili_download.add_argument('-v', '--verbose', action='store_true')
bilibili_download.add_argument('-c', '--cookies', metavar='FILE')
bilibili_download.add_argument('-i', '--info', action='store_true')
bilibili_download.add_argument('-l', '--playlist', action='store_true')
bilibili_download.add_argument('-o', '--output', metavar='dir')
bilibili_download.add_argument('-p', '--parts', nargs='*', metavar='N')
bilibili_download.add_argument('-q', '--qn-want', type=int, metavar='N')
bilibili_download.add_argument('-Q', '--qn-max', type=int, metavar='N', default=116,
                               help='max qn (quality number), default to 116 (1080P60), while qn of 4K is 120.')
bilibili_download.add_argument('-C', '--no-caption', dest='caption', action='store_false')
bilibili_download.add_argument('-A', '--no-moderate-audio', dest='moderate_audio', action='store_false',
                               help='by default the best quality audio is NOT used, '
                                    'instead, a moderate quality (~128kbps) is chose, which is good enough. '
                                    'this option force choosing the best quality audio stream')


def json_edit_func():
    from mylib.os_util import read_json_file, write_json_file, list_files
    from mylib.tricks import eval_or_str
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
json_edit.set_defaults(func=json_edit_func)
json_edit.add_argument('-f', '--file', nargs='?')
json_edit.add_argument('-i', '--indent', type=int, default=4)
json_edit.add_argument('-d', '--delete', action='store_true')
json_edit.add_argument('item', nargs='+')


def json_key_func():
    from mylib.os_util import read_json_file
    args = rtd.args
    d = read_json_file(args.file)
    print(d[args.key])


json_key = add_sub_parser('json.getkey', ['jsk'], 'find in JSON file by key')
json_key.set_defaults(func=json_key_func)
json_key.add_argument('file', help='JSON file to query')
json_key.add_argument('key', help='query key')


def update_json_file():
    from mylib.os_util import read_json_file, write_json_file
    args = rtd.args
    old, new = args.old, args.new
    d = read_json_file(old)
    d.update(read_json_file(new))
    write_json_file(old, d, indent=args.indent)


json_update = add_sub_parser('json.update', ['jsup'], 'update <old> JSON file with <new>')
json_update.set_defaults(func=update_json_file)
json_update.add_argument('old', help='JSON file with old data')
json_update.add_argument('new', help='JSON file with new data')
json_update.add_argument('-t', '--indent', type=int, default=2, metavar='N')


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
    view_similar_images_auto(**kwargs)


img_sim_view = add_sub_parser('img.sim.view', ['vsi'], 'view similar images in current working directory')
img_sim_view.set_defaults(func=view_similar_images)
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
    '--dry-run', action='store_true', help='find similar images, but without viewing them')


def move_ehviewer_images():
    from mylib.ehentai import catalog_ehviewer_images
    args = rtd.args
    catalog_ehviewer_images(dry_run=args.dry_run)


ehv_img_mv = add_sub_parser('ehv.img.mv', ['ehvmv'],
                            'move ehviewer downloaded images into folders')
ehv_img_mv.set_defaults(func=move_ehviewer_images)
ehv_img_mv.add_argument('-D', '--dry-run', action='store_true')

if __name__ == '__main__':
    main()
