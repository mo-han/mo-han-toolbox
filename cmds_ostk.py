#!/usr/bin/env python3
import os.path

from mylib.ext.console_app import *

apr = ArgumentParserWrapper()
an = apr.an
an.l = an.multiline = an.L = an.single_line = an.q = an.quote = ''


def main():
    apr.parse()
    apr.run()


@apr.sub(apr.rpl_dot, aliases=['cb.paths'])
@apr.true(an.L, apr.dst2opt(an.single_line))
@apr.true(an.q, an.quote)
@apr.true('b', 'basename_only')
@apr.map(single_line=an.single_line, quote=an.quote, basename_only='basename_only')
def clipboard_print_paths(single_line=False, quote=False, basename_only=False):
    paths = ostk.clipboard.list_path()
    if basename_only:
        paths = [os.path.basename(i) for i in paths]
    if quote:
        paths = [f'"{p}"' for p in paths]
    if single_line:
        print(' '.join(paths))
    else:
        for p in paths:
            print(p)


if __name__ == '__main__':
    main()
