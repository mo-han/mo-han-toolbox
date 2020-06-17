#!/usr/bin/env python3
# encoding=utf8

import argparse
import cmd
import shlex

import pyperclip

from mylib.os_nt import win32_ctrl_c_signal
from mylib.struct import arg_type_pow2, arg_type_range_factory, ArgumentParserCompactOptionHelpFormatter
from mylib.bilibili import download_bilibili_video

DRAW_LINE_LEN = 32
DRAW_DOUBLE_LINE = '=' * DRAW_LINE_LEN
DRAW_SINGLE_LINE = '-' * DRAW_LINE_LEN
DRAW_UNDER_LINE = '_' * DRAW_LINE_LEN


def argument_parser():
    common_parser_kwargs = {'formatter_class': ArgumentParserCompactOptionHelpFormatter}
    ap = argparse.ArgumentParser(**common_parser_kwargs)
    sub = ap.add_subparsers(title='sub-commands')

    text = 'TEST ONLY'
    test = sub.add_parser(
        'test', help=text, description=text, **common_parser_kwargs)
    test.set_defaults(callee=test_only)

    text = 'bilibili video downloader (source-patched you-get)'
    bilibili_download = sub.add_parser('bilibili.download', aliases=['bldl'], help=text, description=text,
                                       **common_parser_kwargs)
    bilibili_download.set_defaults(callee=bilibili_download_callee)
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

    text = 'query in JSON file'
    json_query = sub.add_parser('json.query', aliases=[], help=text, description=text, **common_parser_kwargs)
    json_query.set_defaults(callee=query_json_file)
    json_query.add_argument('file', help='JSON file to query')
    json_query.add_argument('key', help='query key')

    text = 'update <old> JSON file with <new>'
    json_update = sub.add_parser('json.update', aliases=[], help=text, description=text, **common_parser_kwargs)
    json_update.set_defaults(callee=update_json_file)
    json_update.add_argument('old', help='JSON file with old data')
    json_update.add_argument('new', help='JSON file with new data')

    text = 'line-oriented interactive command mode'
    cmd = sub.add_parser(
        'cmd', aliases=['cli'], help=text, description=text, **common_parser_kwargs)
    cmd.set_defaults(callee=cmd_mode)

    text = 'view similar images in current working directory'
    img_sim_view = sub.add_parser(
        'img.sim.view', aliases=[], help=text, description=text, **common_parser_kwargs)
    img_sim_view.set_defaults(callee=view_similar_images)
    img_sim_view.add_argument(
        '-t', '--thresholds', type=arg_type_range_factory(float, '0<x<=1'), nargs='+', metavar='N'
        , help='(multiple) similarity thresholds')
    img_sim_view.add_argument(
        '-H', '--hashtype', type=str, choices=[s + 'hash' for s in ('a', 'd', 'p', 'w')]
        , help='image hash type')
    img_sim_view.add_argument(
        '-s', '--hashsize', type=arg_type_pow2, metavar='N'
        , help='the side size of the image hash square, must be a integer power of 2')
    img_sim_view.add_argument(
        '-T', '--no-transpose', action='store_false', dest='transpose'
        , help='do not find similar images for transposed variants (rotated, flipped)')
    img_sim_view.add_argument(
        '--dry-run', action='store_true', help='find similar images, but without viewing them')

    text = 'move ehviewer downloaded images into corresponding folders named by the authors'
    ehv_img_mv = sub.add_parser(
        'ehv.img.mv', aliases=[], help=text, description=text, **common_parser_kwargs)
    ehv_img_mv.set_defaults(callee=move_ehviewer_images)
    ehv_img_mv.add_argument('-D', '--dry-run', action='store_true')

    text = 'find URLs from clipboard, and copy them back to clipboard'
    cb_url = sub.add_parser(
        'clipboard.findurl', aliases=['cb.url'], help=text, description=text, **common_parser_kwargs)
    cb_url.set_defaults(callee=url_from_clipboard)
    cb_url.add_argument('pattern', help='URL pattern, or website name')

    return ap


def main():
    ap = argument_parser()
    args = ap.parse_args()
    callee = print
    try:
        callee = args.callee
    except AttributeError:
        ap.print_usage()
        exit()
    callee(args)


class MyKitCmd(cmd.Cmd):
    def __init__(self):
        super(MyKitCmd, self).__init__()
        self.prompt = __class__.__name__ + ':# '
        self._stop = None
        self._done = None

    def precmd(self, line):
        print(DRAW_SINGLE_LINE)
        return line

    def postcmd(self, stop, line):
        if self._done:
            print(DRAW_SINGLE_LINE)
        return self._stop

    def default(self, line):
        try:
            argv_l = shlex.split(line)
            args = argument_parser().parse_args(argv_l)
            callee = args.callee
            if callee not in [cmd_mode, gui_mode]:
                self._done = callee
                return callee(args)
            else:
                self._done = None
        except SystemExit:
            pass

    def do_quit(self, line):
        self._stop = True

    do_exit = do_q = do_quit


def test_only(args):
    print('ok')


def bilibili_download_callee(args: argparse.Namespace):
    download_bilibili_video(**vars(args))


def query_json_file(args):
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
    pattern = args.pattern
    t = pyperclip.paste()
    if pattern == 'pornhub':
        from mylib.pornhub import find_url_from
        urls = find_url_from(t)
    elif pattern == 'youtube':
        from mylib.youtube import find_url_from
        urls = find_url_from(t)
    else:
        from mylib.text import regex_find
        urls = regex_find(pattern, t)
    pyperclip.copy('\n'.join(urls))
    for u in urls:
        print(u)


def cmd_mode(args):
    MyKitCmd().cmdloop()


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
    win32_ctrl_c_signal()
    tidy_ehviewer_images(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
