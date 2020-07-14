#!/usr/bin/env python3
# encoding=utf8

from argparse import ArgumentParser, Namespace
import cmd
import glob
import shlex

from mylib.cli import SimpleCLIDisplay
from mylib.tricks import arg_type_pow2, arg_type_range_factory, ArgParseCompactHelpFormatter, AttrTree

DRAW_LINE_LEN = 32
DRAW_DOUBLE_LINE = '=' * DRAW_LINE_LEN
DRAW_SINGLE_LINE = '-' * DRAW_LINE_LEN
DRAW_UNDER_LINE = '_' * DRAW_LINE_LEN

rte = AttrTree()
cli_draw = SimpleCLIDisplay()
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
            cli_draw.hl()
        self._done = False
        return line

    def postcmd(self, stop, line):
        if self._done:
            cli_draw.hl()
        return self._stop

    def emptyline(self):
        return

    def default(self, line):
        try:
            argv_l = shlex.split(line)
            args = ap.parse_args(argv_l)
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
    from mylib.os_util import ensure_sigint_signal
    ensure_sigint_signal()
    # args, unknown_argv = ap.parse_known_args()
    # if '__unknown__' in args:
    #     del args.__unknown__
    #     rte.args = args
    #     rte.unknown_argv = unknown_argv
    # else:
    #     rte.args = ap.parse_args()
    #     rte.unknown_argv = None
    # try:
    #     func = rte.args.func
    rte.args = args = ap.parse_args()
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


def iwara_dl_func():
    from mylib.iwara import youtube_dl_main_x_iwara
    import sys
    sys.argv[0] = ' '.join(sys.argv[:2])
    youtube_dl_main_x_iwara(rte.args.argv)


iwara_dl = add_sub_parser('iwara.dl', ['iwrdl'], 'modified youtube-dl for iwara.tv (fix issue of missing uploader)')
iwara_dl.set_defaults(func=iwara_dl_func)
iwara_dl.add_argument('argv', nargs='*', help='argument(s) propagated to youtube-dl, better put a -- before it')


def rename_func():
    from mylib.os_util import regex_move_path
    args = rte.args
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
    args = rte.args
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


def dukto_to_clipboard_func():
    from mylib.dukto import run, recv_text_into_clipboard, config
    from threading import Thread
    from queue import Queue
    config(server_text_queue=Queue())
    t = Thread(target=recv_text_into_clipboard)
    t.daemon = True
    t.start()
    run()


dukto_to_clipboard = add_sub_parser('dukto.to.clipboard', ['dukto.cb', 'duktocb'],
                                    'put text received in dukto into clipboard')
dukto_to_clipboard.set_defaults(func=dukto_to_clipboard_func)


def url_from_clipboard():
    import pyperclip
    from mylib.text import regex_find
    from mylib.web import decode_html_char_ref
    args = rte.args
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
    args = rte.args
    PotPlayerKit().rename_file_gui(alt_tab=args.no_keep_front)


potplayer_rename = add_sub_parser('potplayer.rename', ['pp.ren', 'ppren'], 'rename media file opened in PotPlayer')
potplayer_rename.set_defaults(func=potplayer_rename_func)
potplayer_rename.add_argument('-F', '--no-keep-front', action='store_true', help='do not keep PotPlayer in front')


def bilibili_download_func():
    from mylib.bilibili import download_bilibili_video
    args = rte.args
    download_bilibili_video(**vars(args))


bilibili_download = add_sub_parser('bilibili.download', ['bldl'], 'bilibili video downloader (source-patched you-get)')
bilibili_download.set_defaults(func=bilibili_download_func)
bilibili_download.add_argument('url')
bilibili_download.add_argument('-c', '--cookies')
bilibili_download.add_argument('-i', '--info', action='store_true')
bilibili_download.add_argument('-l', '--playlist', action='store_true')
bilibili_download.add_argument('-o', '--output', metavar='dir')
bilibili_download.add_argument('-p', '--parts', nargs='*', type=int, metavar='N')
bilibili_download.add_argument('-q', '--qn-want', type=int, metavar='N')
bilibili_download.add_argument('-Q', '--qn-max', type=int, metavar='N')
bilibili_download.add_argument('-C', '--no-caption', dest='caption', action='store_false')
bilibili_download.add_argument('-A', '--no-moderate-audio', dest='moderate_audio', action='store_false')


def json_key_func():
    from json import load
    args = rte.args
    with open(args.file) as f:
        d = load(f)
    print(d[args.key])


json_key = add_sub_parser('json.getkey', ['jsk'], 'find in JSON file by key')
json_key.set_defaults(func=json_key_func)
json_key.add_argument('file', help='JSON file to query')
json_key.add_argument('key', help='query key')


def update_json_file():
    from json import load, dump
    args = rte.args
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
    args = rte.args
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
    args = rte.args
    tidy_ehviewer_images(dry_run=args.dry_run)


ehv_img_mv = add_sub_parser('ehv.img.mv', ['ehvmv'],
                            'move ehviewer downloaded images into corresponding folders named by the authors')
ehv_img_mv.set_defaults(func=move_ehviewer_images)
ehv_img_mv.add_argument('-D', '--dry-run', action='store_true')

if __name__ == '__main__':
    main()
