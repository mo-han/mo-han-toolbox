#!/usr/bin/env python3
from mylib.ex.console_app import *

apr = ArgumentParserRigger()
an = apr.an
an.l = an.multiline = an.L = an.single_line = an.q = an.quote = ''


def main():
    apr.parse()
    apr.run()


@apr.sub(apr.rnu(), aliases=['cb.paths'])
@apr.true(an.L, apr.dst2opt(an.single_line))
@apr.true(an.q, an.quote)
@apr.map(single_line=an.single_line, quote=an.quote)
def clipboard_print_paths(single_line=False, quote=False):
    paths = ostk.clipboard.list_path()
    if quote:
        paths = [f'"{p}"' for p in paths]
    if single_line:
        print(' '.join(paths))
    else:
        for p in paths:
            print(p)


if __name__ == '__main__':
    main()
