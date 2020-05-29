#!/usr/bin/env python3
# encoding=utf8

import argparse
import cmd
import shlex

from lib_hentai import tidy_ehviewer_images
from lib_image import view_similar_images_auto
from lib_misc import win32_ctrl_c
from lib_struct import arg_type_pow2, arg_type_range_factory, ArgumentParserCompactOptionHelpFormatter

DRAW_LINE_LEN = 32
DRAW_DOUBLE_LINE = '=' * DRAW_LINE_LEN
DRAW_SINGLE_LINE = '-' * DRAW_LINE_LEN
DRAW_UNDER_LINE = '_' * DRAW_LINE_LEN


def argument_parser():
    common_parser_kwargs = {'formatter_class': ArgumentParserCompactOptionHelpFormatter}
    ap = argparse.ArgumentParser(**common_parser_kwargs)
    sub = ap.add_subparsers(title='sub-commands')

    text = 'for text only'
    sub_test = sub.add_parser(
        'test', help=text, description=text, **common_parser_kwargs)
    sub_test.set_defaults(callee=test)

    text = 'line-oriented interactive command mode'
    sub_cmd = sub.add_parser(
        'cmd', aliases=['cli'], help=text, description=text, **common_parser_kwargs)
    sub_cmd.set_defaults(callee=cmd_mode)

    text = 'view similar images in current working directory'
    sub_image_similar_view = sub.add_parser(
        'vwsimimg', aliases=['vsi'], help=text, description=text, **common_parser_kwargs)
    sub_image_similar_view.set_defaults(callee=view_similar_images)
    sub_image_similar_view.add_argument(
        '-t', '--thresholds', type=arg_type_range_factory(float, '0<x<=1'), nargs='+', metavar='N'
        , help='(multiple) similarity thresholds')
    sub_image_similar_view.add_argument(
        '-H', '--hashtype', type=str, choices=[s + 'hash' for s in ('a', 'd', 'p', 'w')]
        , help='image hash type')
    sub_image_similar_view.add_argument(
        '-s', '--hashsize', type=arg_type_pow2, metavar='N'
        , help='the side size of the image hash square, must be a integer power of 2')
    sub_image_similar_view.add_argument(
        '-T', '--no-transpose', action='store_false', dest='transpose'
        , help='do not find similar images for transposed variants (rotated, flipped)')
    sub_image_similar_view.add_argument(
        '--dry', action='store_true', help='find similar images, but without viewing them')

    text = 'move ehviewer downloaded images into corresponding folders named by the authors'
    sub_move_ehviewer_images = sub.add_parser(
        'mvehv', aliases=[], help=text, description=text, **common_parser_kwargs)
    sub_move_ehviewer_images.set_defaults(callee=move_ehviewer_images)

    return ap


def main():
    args = argument_parser().parse_args()
    args.callee(args)


class MyKitCmd(cmd.Cmd):
    def __init__(self):
        super(MyKitCmd, self).__init__()
        self.prompt = ':# '
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


def test(args):
    print('ok')


def cmd_mode(args):
    MyKitCmd().cmdloop()


def gui_mode(args):
    pass


def view_similar_images(args: argparse.Namespace):
    kwargs = {
        'thresholds': args.thresholds,
        'hashtype': args.hashtype,
        'hashsize': args.hashsize,
        'trans': args.transpose,
        'dryrun': args.dry,
    }
    view_similar_images_auto(**kwargs)


def move_ehviewer_images(args):
    win32_ctrl_c()
    tidy_ehviewer_images()


if __name__ == '__main__':
    main()
