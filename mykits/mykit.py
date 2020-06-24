#!/usr/bin/env python3
# encoding=utf8

import argparse
import cmd
import shlex

from mylib.cli import SimpleDrawer

DRAW_LINE_LEN = 32
DRAW_DOUBLE_LINE = '=' * DRAW_LINE_LEN
DRAW_SINGLE_LINE = '-' * DRAW_LINE_LEN
DRAW_UNDER_LINE = '_' * DRAW_LINE_LEN

cli_draw = SimpleDrawer()


def argument_parser():
    from mylib.tricks import arg_type_pow2, arg_type_range_factory, ArgumentParserCompactOptionHelpFormatter
    common_parser_kwargs = {'formatter_class': ArgumentParserCompactOptionHelpFormatter}
    ap = argparse.ArgumentParser(**common_parser_kwargs)
    sub = ap.add_subparsers(title='sub-commands')

    def add_parser(name: str, aliases: list, desc: str):
        def decorator(f):
            def decorated_f():
                return sub.add_parser(name, aliases=aliases, help=desc, description=desc, **common_parser_kwargs)

            return decorated_f

        return decorator

    @add_parser('test', [], 'for testing...')
    def test(): pass

    test = test()
    test.set_defaults(func=test_only)

    @add_parser('cmd', ['cli'],
                'command line oriented interactive mode')
    def cmd_mode(): pass

    cmd_mode = cmd_mode()
    cmd_mode.set_defaults(func=cmd_mode_func)

    @add_parser('clipboard.findurl', ['cb.url', 'cburl'],
                'find URLs from clipboard, then copy found URLs back to clipboard')
    def clipboard_findurl(): pass

    clipboard_findurl = clipboard_findurl()
    clipboard_findurl.set_defaults(func=url_from_clipboard)
    clipboard_findurl.add_argument('pattern', help='URL pattern, or website name')

    @add_parser('clipboard.rename', ['cb.ren', 'cbren'],
                'rename files in clipboard')
    def clipboard_rename(): pass

    clipboard_rename = clipboard_rename()
    clipboard_rename.set_defaults(func=clipboard_rename_func)

    @add_parser('potplayer.rename', ['pp.ren', 'ppren'],
                'rename media file opened in PotPlayer')
    def potplayer_rename(): pass

    potplayer_rename = potplayer_rename()
    potplayer_rename.set_defaults(func=potplayer_rename_func)

    @add_parser('bilibili.download', ['bldl'],
                'bilibili video downloader (source-patched you-get)')
    def bilibili_download(): pass

    bilibili_download = bilibili_download()
    bilibili_download.set_defaults(func=bilibili_download_func)
    bilibili_download.add_argument('url')
    bilibili_download.add_argument('-c', '--cookies')
    bilibili_download.add_argument('-i', '--info', action='store_true')
    bilibili_download.add_argument('-l', '--playlist', action='store_true')
    bilibili_download.add_argument('-o', '--output', metavar='dir')
    bilibili_download.add_argument('-p', '--parts', nargs='*', type=int, metavar='N')
    bilibili_download.add_argument('-q', '--qn-single', type=int, metavar='N')
    bilibili_download.add_argument('-Q', '--qn-max', type=int, metavar='N')
    bilibili_download.add_argument('-C', '--no-caption', dest='caption', action='store_false')
    bilibili_download.add_argument('-A', '--no-moderate-audio', dest='moderate_audio', action='store_false')

    @add_parser('json.getkey', ['jsk'],
                'find in JSON file by key')
    def json_key(): pass

    json_key = json_key()
    json_key.set_defaults(func=json_key_func)
    json_key.add_argument('file', help='JSON file to query')
    json_key.add_argument('key', help='query key')

    @add_parser('json.update', ['jsup'],
                'update <old> JSON file with <new>')
    def json_update(): pass

    json_update = json_update()
    json_update.set_defaults(func=update_json_file)
    json_update.add_argument('old', help='JSON file with old data')
    json_update.add_argument('new', help='JSON file with new data')

    @add_parser('img.sim.view', ['vsi'],
                'view similar images in current working directory')
    def img_sim_view(): pass

    img_sim_view = img_sim_view()
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

    @add_parser('ehv.img.mv', ['ehvmv'],
                'move ehviewer downloaded images into corresponding folders named by the authors')
    def ehv_img_mv(): pass

    ehv_img_mv = ehv_img_mv()
    ehv_img_mv.set_defaults(func=move_ehviewer_images)
    ehv_img_mv.add_argument('-D', '--dry-run', action='store_true')

    return ap


def main():
    from mylib.osutil import ensure_sigint_signal
    ensure_sigint_signal()
    ap = argument_parser()
    args = ap.parse_args()
    try:
        func = args.func
    except AttributeError:
        func = cmd_mode_func
    func(args)


class MyKitCmd(cmd.Cmd):
    def __init__(self):
        super(MyKitCmd, self).__init__()
        self.prompt = __class__.__name__ + ':# '
        self._stop = None
        self._done = None

    def precmd(self, line):
        cli_draw.hl()
        return line

    def postcmd(self, stop, line):
        if self._done:
            cli_draw.hl()
        return self._stop

    def default(self, line):
        try:
            argv_l = shlex.split(line)
            args = argument_parser().parse_args(argv_l)
            func = args.func
            if func not in [cmd_mode_func, gui_mode]:
                self._done = func
                return func(args)
            else:
                self._done = None
        except SystemExit:
            pass

    def do_quit(self, line):
        self._stop = True

    do_exit = do_q = do_quit


def cmd_mode_func(args):
    MyKitCmd().cmdloop()


def test_only(args):
    print('ok')


def clipboard_rename_func(args):
    from mylib.gui import rename_dialog
    from mylib.osutil import clipboard
    for f in clipboard.get_path():
        rename_dialog(f)


def potplayer_rename_func(args):
    from mylib.potplayer import PotPlayerKit
    PotPlayerKit().rename_file_gui()


def bilibili_download_func(args: argparse.Namespace):
    from mylib.bilibili import download_bilibili_video
    download_bilibili_video(**vars(args))


def json_key_func(args):
    from json import load
    with open(args.file) as f:
        d = load(f)
    print(d[args.key])


def update_json_file(args):
    from json import load, dump
    old, new = args.old, args.new
    with open(old) as f:
        d = load(f)
    with open(new) as f:
        d.update(load(f))
    with open(old, 'w') as f:
        dump(d, f)


def url_from_clipboard(args):
    import pyperclip
    pattern = args.pattern
    t = pyperclip.paste()
    if pattern == 'pornhub':
        from mylib.pornhub import find_url_in_text
        urls = find_url_in_text(t)
    elif pattern == 'youtube':
        from mylib.youtube import find_url_in_text
        urls = find_url_in_text(t)
    else:
        from mylib.text import regex_find
        urls = regex_find(pattern, t)
    pyperclip.copy('\n'.join(urls))
    print(urls)


def gui_mode(args):
    pass


def view_similar_images(args: argparse.Namespace):
    from mylib.image import view_similar_images_auto
    kwargs = {
        'thresholds': args.thresholds,
        'hashtype': args.hashtype,
        'hashsize': args.hashsize,
        'trans': args.transpose,
        'dryrun': args.dry_run,
    }
    view_similar_images_auto(**kwargs)


def move_ehviewer_images(args):
    from mylib.ehentai import tidy_ehviewer_images
    tidy_ehviewer_images(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
