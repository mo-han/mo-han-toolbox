#!/usr/bin/env python3
# encoding=utf8

import argparse

from lib_image import view_similar_images_auto
from lib_misc import ArgumentParserCompactOptionHelpFormatter, arg_type_range_factory, arg_type_pow2


def parse_args():
    common_parser_kwargs = {'formatter_class': ArgumentParserCompactOptionHelpFormatter}
    ap = argparse.ArgumentParser(**common_parser_kwargs)
    sub_image = ap.add_subparsers(title='commands for image files')

    text = 'view similar images in current working directory'
    sub_image_similar_view = sub_image.add_parser(
        'vwsimimg', aliases=['vsi'], help=text, description=text, **common_parser_kwargs)
    sub_image_similar_view.set_defaults(callee=_view_similar_images)
    sub_image_similar_view.add_argument(
        '-t', '--thresholds', type=arg_type_range_factory(float, '0<x<=1'), nargs='+', metavar='n'
        , help='(multiple) similarity thresholds')
    sub_image_similar_view.add_argument(
        '-H', '--hashtype', type=str, choices=[s + 'hash' for s in ('a', 'd', 'p', 'w')]
        , help='image hash type')
    sub_image_similar_view.add_argument(
        '-s', '--hashsize', type=arg_type_pow2, metavar='n'
        , help='the side size of the image hash square, must be a integer power of 2')
    sub_image_similar_view.add_argument(
        '-T', '--no-transpose', action='store_false', dest='transpose'
        , help='do not find similar images for transposed variants')
    sub_image_similar_view.add_argument(
        '--dry', action='store_true', help='find similar images, but without viewing them')

    return ap.parse_args()


def main():
    args = parse_args()
    args.callee(args)


def _view_similar_images(args: argparse.Namespace):
    kwargs = {
        'thresholds': args.thresholds,
        'hashtype': args.hashtype,
        'hashsize': args.hashsize,
        'trans': args.transpose,
        'dryrun': args.dry
    }
    view_similar_images_auto(**kwargs)


if __name__ == '__main__':
    main()
