#!/usr/bin/env python3
# encoding=utf8
"""This tool heavily depends on `mylib` package, make sure `mylib` folder is in the same path with this tool."""

import cmd
import glob
import shlex
import sys
from argparse import ArgumentParser, REMAINDER

from mylib.cli import LinePrinter
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
            cli_draw.hl(shorter=1)
        self._done = False
        return line

    def postcmd(self, stop, line):
        if self._done:
            cli_draw.hl(shorter=1)
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


def ffconv_func():
    from mylib.ffmpeg import preset_video_convert
    content = rtd.args.content
    codec = rtd.args.codec

ffconv = add_sub_parser('ffconv', [], 'convert video file by ffmpeg')
ffconv.set_defaults(func=ffconv_func)
ffconv.add_argument('source')
ffconv.add_argument('-t', '--content', choices=('cgi', 'film'))
ffconv.add_argument('-c', '--codec', choices=('a', 'h'))
ffconv.add_argument('-q', '--quality-crf', type=float)
ffconv.add_argument('-a', '--hw-accel', choices=('q', 'qsv'))
ffconv.add_argument('-w', '--within-res', choices=('fhd', 'hd'))
ffconv.add_argument('-o', )


def ffprobe_func():
    from ffmpeg import probe
    from pprint import pprint
    file = rtd.args.file
    ss = rtd.args.select_streams
    if not file:
        from mylib.os_util import clipboard as cb
        file = cb.get_path()[0]
    if ss:
        pprint(probe(file, select_streams=ss))
    else:
        pprint(probe(file))


ffprobe = add_sub_parser('ffprobe', [], 'json format ffprobe on a file')
ffprobe.set_defaults(func=ffprobe_func)
ffprobe.add_argument('-s', '--select-streams')
ffprobe.add_argument('file', nargs='?')


def file_type_func():
    from filetype import guess
    files = rtd.args.file
    if rtd.args.print_no_file:
        fmt = '{type}'
    else:
        fmt = '{type} ({file})'
    if not files:
        from mylib.os_util import clipboard
        files = clipboard.get_path()
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
    sys.argv = [argv0] + rtd.args.argv
    libpip2pi_commands_x.pip2pi(['pip2pi'] + rtd.args.argv)


pip2pi = add_sub_parser('pip2pi', [], 'modified pip2pi (from pip2pi)')
pip2pi.set_defaults(func=pip2pi_func)
pip2pi.add_argument('argv', nargs='*')


def dir2pi_func():
    from mylib.pip2pi_x import libpip2pi_commands_x
    import sys
    argv0 = ' '.join(sys.argv[:2]) + ' --'
    sys.argv = [argv0] + rtd.args.argv
    libpip2pi_commands_x.dir2pi(['dir2pi'] + rtd.args.argv)


dir2pi = add_sub_parser('dir2pi', [], 'modified dir2pi (from pip2pi)')
dir2pi.set_defaults(func=dir2pi_func)
dir2pi.add_argument('argv', nargs='*')


def iwara_dl_func():
    from mylib.iwara import youtube_dl_main_x_iwara
    import sys
    argv0 = ' '.join(sys.argv[:2]) + ' --'
    sys.argv = [argv0] + rtd.args.argv
    youtube_dl_main_x_iwara()


iwara_dl = add_sub_parser('iwara.dl', ['iwrdl'], 'modified youtube-dl for iwara.tv (fixing issue of missing uploader)')
iwara_dl.set_defaults(func=iwara_dl_func)
iwara_dl.add_argument('argv', nargs='*', help='argument(s) propagated to youtube-dl, better put a -- before it')


def rename_func():
    from mylib.os_util import regex_move_path
    args = rtd.args
    source = args.source
    pattern = args.pattern
    replace = args.replace
    only_basename = args.only_basename
    dry_run = args.dry_run
    for src_path in glob.glob(source):
        try:
            regex_move_path(src_path, pattern, replace, only_basename, dry_run)
        except OSError as e:
            print(repr(e))


rename = add_sub_parser('rename', ['ren', 'rn'], 'rename file(s) or folder(s)')
rename.set_defaults(func=rename_func)
rename.add_argument('-B', '-not-only-basename', dest='only_basename', action='store_false')
rename.add_argument('-D', '--dry-run', action='store_true')
rename.add_argument('source')
rename.add_argument('pattern')
rename.add_argument('replace')


def run_from_lines_func():
    import os
    from mylib.os_util import clipboard
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
    for line in lines:
        if not line:
            continue
        command = cmd_fmt.format(line.strip())
        print('#', command)
        if not dry_run:
            os.system(command)


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
    from mylib.os_util import clipboard
    for f in clipboard.get_path():
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


def json_key_func():
    from json import load
    args = rtd.args
    with open(args.file) as f:
        d = load(f)
    print(d[args.key])


json_key = add_sub_parser('json.getkey', ['jsk'], 'find in JSON file by key')
json_key.set_defaults(func=json_key_func)
json_key.add_argument('file', help='JSON file to query')
json_key.add_argument('key', help='query key')


def update_json_file():
    from json import load, dump
    args = rtd.args
    old, new = args.old, args.new
    with open(old) as f:
        d = load(f)
    with open(new) as f:
        d.update(load(f))
    with open(old, 'w') as f:
        dump(d, f)


json_update = add_sub_parser('json.update', ['jsup'], 'update <old> JSON file with <new>')
json_update.set_defaults(func=update_json_file)
json_update.add_argument('old', help='JSON file with old data')
json_update.add_argument('new', help='JSON file with new data')


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
    from mylib.ehentai import tidy_ehviewer_images
    args = rtd.args
    tidy_ehviewer_images(dry_run=args.dry_run)


ehv_img_mv = add_sub_parser('ehv.img.mv', ['ehvmv'],
                            'move ehviewer downloaded images into corresponding folders named by the authors')
ehv_img_mv.set_defaults(func=move_ehviewer_images)
ehv_img_mv.add_argument('-D', '--dry-run', action='store_true')

if __name__ == '__main__':
    main()
