#!/usr/bin/env python3
# encoding=utf8
"""This tool heavily depends on `mylib` package, make sure `mylib` folder is in the same path with this tool."""

import cmd
import os
import re
import shlex
import sys
from argparse import ArgumentParser, REMAINDER
from pprint import pprint

from send2trash import send2trash

from mylib import fs_util
from mylib._deprecated import fs_find_iter, real_join_path, fs_inplace_rename, fs_inplace_rename_regex
from mylib.os_util import clipboard, list_files, shrink_name_middle, \
    set_console_title___try
from mylib.tricks import arg_type_pow2, arg_type_range_factory, ArgParseCompactHelpFormatter, Attreebute, \
    deco_factory_keyboard_interrupt
from mylib.tui_ import LinePrinter

rtd = Attreebute()  # runtime data
tui_lp = LinePrinter()
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
    set_console_title___try(MyKitCmd.__name__)
    MyKitCmd().cmdloop()


cmd_mode = add_sub_parser('cmd', ['cli'], 'command line interactive mode')
cmd_mode.set_defaults(func=cmd_mode_func)


def cfip_func():
    from mylib.websites import get_cloudflare_ipaddr_hostmonit
    from mylib.fs_util import write_json_file
    from pprint import pformat
    args = rtd.args
    file = args.file
    in_list = args.list
    isp = args.isp
    hostname = args.hostname

    data = get_cloudflare_ipaddr_hostmonit()
    info: dict = data['info']
    if isp:
        info = {isp: info[isp]}
    if in_list:
        lines = []
        for ip_isp, ip_l in info.items():
            lines.append(ip_isp)
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


cfip = add_sub_parser('cloudflare.ipaddr.hostmonit', ['cfip'], 'get recommended ip addresses from hostmonit.com')
cfip.set_defaults(func=cfip_func)
cfip.add_argument('file', help='write whole data to JSON file', nargs='?')
cfip.add_argument('-L', '--list', action='store_true')
cfip.add_argument('-P', '--isp', choices=('CM', 'CT', 'CU'))
cfip.add_argument('-H', '--hostname')


def video_guess_crf_func():
    from mylib.ffmpeg_local_alpha import guess_video_crf, file_is_video
    args = rtd.args
    path_l = [path for path in list_files(args.src or clipboard) if file_is_video(path)]
    codec = args.codec
    work_dir = args.work_dir
    redo = args.redo
    auto_clean = not args.no_clean
    for path in path_l:
        tui_lp.l()
        tui_lp.p(path)
        tui_lp.p(guess_video_crf(src=path, codec=codec, work_dir=work_dir, redo=redo, auto_clean=auto_clean))


video_guess_crf = add_sub_parser('video.crf.guess', ['crf'], 'guess CRF parameter value of video file')
video_guess_crf.set_defaults(func=video_guess_crf_func)
video_guess_crf.add_argument('src', nargs='*')
video_guess_crf.add_argument('-c', '--codec', nargs='?')
video_guess_crf.add_argument('-w', '--work-dir')
video_guess_crf.add_argument('-R', '--redo', action='store_true')
video_guess_crf.add_argument('-L', '--no-clean', action='store_true')


def dir_flatter_func():
    import shutil
    args = rtd.args
    src = args.src or clipboard.list_paths()
    for s in src:
        if not os.path.isdir(s):
            print(f'! skip non-folder: {s}')
            continue
        with fs_util.ctx_pushd(s):
            dir_l = list(fs_find_iter(find_dir_instead_of_file=True))
            if not dir_l:
                continue
            file_l = list(fs_find_iter(strip_root=True, recursive=True))
            for fp in file_l:
                flat_path = shrink_name_middle(fs_util.safe_name(fp))
                shutil.move(fp, flat_path)
            for dp in dir_l:
                os.removedirs(dp)


dir_flatter = add_sub_parser('dir.flatter', ['flat.dir', 'flat.folder'],
                             'flatten directory tree inside a directory into files')
dir_flatter.set_defaults(func=dir_flatter_func)
dir_flatter.add_argument('src', nargs='*')


@deco_factory_keyboard_interrupt(2)
def put_in_dir_func():
    from mylib.os_util import path_or_glob, fs_move_cli
    from mylib.text import find_words
    from mylib.tui_ import prompt_choose_number, prompt_confirm
    conf_file = real_join_path('~', '.config', 'fs.put_in_dir.json')
    conf = fs_util.read_json_file(conf_file) or {'dst_map': {}}
    dst_map = conf['dst_map']
    args = rtd.args
    src = args.src or clipboard.list_paths()
    dst = args.dst
    alias = args.alias
    dry_run = args.dry_run
    sub_dir = args.sub_dir
    pattern = args.pattern
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
    fs_util.write_json_file(conf_file, conf, indent=4)
    if not dst:
        return
    dst = dst_map.get(dst, dst)
    if os.path.isfile(dst):
        print(f'! {dst} is file (should be directory)', file=sys.stderr)
        exit(1)
    os.makedirs(dst, exist_ok=True)
    db_path = fs_util.make_path(dst, '__folder_name_words__.db')
    db = fs_util.read_sqlite_dict_file(db_path)
    sub_dirs_d = {b: set(find_words(b.lower())) for b in next(os.walk(dst))[1] if b not in db}
    sub_dirs_d.update(db)
    for ss in src:
        for s in path_or_glob(ss):
            tui_lp.d()
            if sub_dir:
                source_words_l = filename_words(os.path.basename(s).lower())
                source_words_set = set(source_words_l)
                similar_d = {basename: source_words_set & words_set for basename, words_set in sub_dirs_d.items()}
                similar_d = {k: v for k, v in similar_d.items() if v}
                similar_l = sorted(similar_d, key=lambda x: similar_d[x], reverse=True)
                if similar_l:
                    target_dir_name = prompt_choose_number(f'Select probable folder for\n{s}', similar_l)
                    tui_lp.l()
                else:
                    target_dir_name = None
                target_dir_name = target_dir_name or input(f'Create folder for\n{s}: ')
                if target_dir_name:
                    sub_dirs_d[target_dir_name] = set(find_words(target_dir_name.lower()))
                    dir_path = fs_util.make_path(dst, target_dir_name)
                    if not dry_run:
                        os.makedirs(dir_path, exist_ok=True)
                else:
                    dir_path = dst
            else:
                dir_path = dst
            d = fs_util.make_path(dir_path, os.path.basename(s))
            if os.path.exists(d):
                if not prompt_confirm(f'Overwrite {d}?', default=False):
                    continue
            if not dry_run:
                fs_move_cli(s, d)
            print(f'{s} -> {d}')
    fs_util.write_sqlite_dict_file(db_path, sub_dirs_d, update_only=True)


put_in_dir = add_sub_parser('putindir', ['mvd'], 'put files/folders into dest dir')
put_in_dir.set_defaults(func=put_in_dir_func)
put_in_dir.add_argument('-D', '--dry-run', action='store_true')
put_in_dir.add_argument('-a', '--alias', nargs='*', help='list, show, set or delete dst mapping aliases')
put_in_dir.add_argument('-d', '--sub-dir', action='store_true', help='into sub-directory by name')
put_in_dir.add_argument('-p', '--pattern')
put_in_dir.add_argument('dst', nargs='?', help='dest dir')
put_in_dir.add_argument('src', nargs='*')


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


files_clear_redundant = add_sub_parser('file.clear.redundant', ['fcr'], 'clear files with related names')
fcr = files_clear_redundant
fcr.set_defaults(func=clear_redundant_files_func)
fcr.add_argument('-t', '--tails-keep', nargs='*', metavar='tail', help='keep files with these tails')
fcr.add_argument('-x', '--extensions-keep', nargs='*', metavar='ext', help='keep files with these extensions')
fcr.add_argument('-T', '--tails-gone', nargs='*', metavar='tail', help='remove files with these tails')
fcr.add_argument('-X', '--extensions-gone', nargs='*', metavar='ext', help='remove files with these extensions')
fcr.add_argument('-D', '--dry-run', action='store_true')
fcr.add_argument('src', nargs='*')


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
cookies_write.set_defaults(func=cookies_write_func)
cookies_write.add_argument('file', nargs='*')
cookies_write.add_argument('-v', '--verbose', action='store_true')


def ccj_func():
    from mylib.web_client import convert_cookies_file_json_to_netscape
    files = rtd.args.file or list_files(clipboard, recursive=False)
    for fp in files:
        print(f'* {fp}')
        convert_cookies_file_json_to_netscape(fp)


cookies_conv_json = add_sub_parser('cookies.conv.json', ['ccj'], 'convert .json cookies file')
cookies_conv_json.set_defaults(func=ccj_func)
cookies_conv_json.add_argument('file', nargs='*')


def ffmpeg_img2vid_func():
    from mylib.ffmpeg_local_alpha import FFmpegRunnerAlpha, FFmpegArgsList, parse_kw_opt_str
    ff = FFmpegRunnerAlpha(banner=False, overwrite=True)
    ff.logger.setLevel('INFO')
    args = rtd.args
    images = args.images
    output = args.output
    res_fps = args.res_fps
    keywords = args.keyword or ()
    ffmpeg_options = args.opt or ()
    output_args = FFmpegArgsList()
    if os.path.isdir(os.path.dirname(images)):
        images_l = [images]
    else:
        images_l = [os.path.join(folder, images) for folder in clipboard.list_paths() if os.path.isdir(folder)]
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


ffmpeg_img2vid = add_sub_parser('wrap.ffmpeg.img2vid', ['img2vid'], 'convert images (frames) into video using ffmpeg')
ffmpeg_img2vid.set_defaults(func=ffmpeg_img2vid_func)
ffmpeg_img2vid.add_argument('-i', '--images', help='input images, e.g. "%%03d.jpg"', required=True)
ffmpeg_img2vid.add_argument('-o', '--output', help='output video', required=True)
ffmpeg_img2vid.add_argument('-r', '--res-fps', metavar='WxH@FPS', required=True)
ffmpeg_img2vid.add_argument('-k', '--keyword', nargs='*')
ffmpeg_img2vid.add_argument('opt', help='ffmpeg options (better insert -- before them)', nargs='*')


def ffmpeg_func():
    from mylib.ffmpeg_local_alpha import kw_video_convert
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
    kw_video_convert(source=source, keywords=keywords, vf=video_filters, cut_points=cut_points, dest=output_path,
                     overwrite=overwrite, redo=redo_origin, verbose=verbose, dry_run=dry_run, ffmpeg_opts=opts)


ffmpeg = add_sub_parser('wrap.ffmpeg', ['ffmpeg', 'ff'], 'convert video file using ffmpeg')
ffmpeg.set_defaults(func=ffmpeg_func)
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
    from mylib.os_util import list_files, list_dirs
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
regex_rename.set_defaults(func=regex_rename_func)
regex_rename.add_argument('-B', '-not-only-basename', dest='only_basename', action='store_false')
regex_rename.add_argument('-D', '--dry-run', action='store_true')
regex_rename.add_argument('-d', '--only-dirs', action='store_true')
regex_rename.add_argument('-s', '--source')
regex_rename.add_argument('-r', '--recursive', action='store_true')
regex_rename.add_argument('pattern')
regex_rename.add_argument('replace')


def rename_func():
    from mylib.os_util import list_files, list_dirs
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
rename.set_defaults(func=rename_func)
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
dukto_x.set_defaults(func=dukto_x_func)
dukto_x.add_argument('-f', '--copy-text-to-file', metavar='file', dest='file')
dukto_x.add_argument('-c', '--copy-text-to-clipboard', action='store_true', dest='clipboard')
dukto_x.add_argument('-e', '--echo', action='store_true')
dukto_x.add_argument('ndrop_args', metavar='[--] arguments for ndrop', nargs=REMAINDER)


def url_from_clipboard():
    import pyperclip
    from mylib.text import regex_find
    from html import unescape
    args = rtd.args
    pattern = args.pattern
    t = pyperclip.paste()
    if not pattern:
        urls = []
    elif pattern == 'ed2k':
        p = r'ed2k://[^/]+/'
        urls = regex_find(p, t, dedup=True)
    elif pattern == 'magnet':
        p = r'magnet:[^\s"]+'
        urls = regex_find(p, unescape(t), dedup=True)
    elif pattern == 'iwara':
        from mylib.website_iwara import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern in ('pornhub', 'ph'):
        from mylib.website_ph import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern in ('youtube', 'ytb'):
        from mylib.website_yt import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern in ('bilibili', 'bili'):
        from mylib.website_bili import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern in ('hc.fyi', 'hentai.cafe', 'hentaicafe'):
        p = r'https://hentai.cafe/hc.fyi/\d+'
        urls = regex_find(p, t, dedup=True)
    else:
        urls = regex_find(pattern, t)
    urls = '\r\n'.join(urls)
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
    from mylib.website_bili import download_bilibili_video
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
bilibili_download.add_argument('-l', '--playlist', action='store_true', help='BUGGY! DO NOT USE!')
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
    from mylib.os_util import list_files
    from mylib.fs_util import write_json_file
    from mylib.fs_util import read_json_file
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
    from mylib.fs_util import read_json_file
    args = rtd.args
    d = read_json_file(args.file)
    print(d[args.key])


json_key = add_sub_parser('json.getkey', ['jsk'], 'find in JSON file by key')
json_key.set_defaults(func=json_key_func)
json_key.add_argument('file', help='JSON file to query')
json_key.add_argument('key', help='query key')


def update_json_file():
    from mylib.fs_util import write_json_file
    from mylib.fs_util import read_json_file
    args = rtd.args
    old, new = args.old, args.new
    d = read_json_file(old)
    d.update(read_json_file(new))
    write_json_file(old, d, indent=args.indent)


json_update = add_sub_parser('json.update', ['jsup'], 'update <old> JSON file with <new>')
json_update.set_defaults(func=update_json_file)
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
    from mylib.website_eh import catalog_ehviewer_images
    args = rtd.args
    catalog_ehviewer_images(dry_run=args.dry_run)


ehv_img_mv = add_sub_parser('ehv.img.mv', ['ehvmv'],
                            'move ehviewer downloaded images into folders')
ehv_img_mv.set_defaults(func=move_ehviewer_images)
ehv_img_mv.add_argument('-D', '--dry-run', action='store_true')

if __name__ == '__main__':
    main()
