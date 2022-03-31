#!/usr/bin/env python3
from ezpykitext.extlib.termcolor import *
from ezpykitext.appkit import *
from ezpykitext.webclient import *

apr = argparse.ArgumentParserWrapper()


def main():
    apr.parse()
    apr.run()


@apr.sub(aliases=['cvck'])
@apr.opt('s', 'src')
@apr.opt('d', 'dst')
@apr.true('v', 'verbose')
@apr.map('src', 'dst', verbose='verbose')
def convert_cookies(src, dst, verbose=False):
    src = get_from_source(src)
    if verbose:
        cprint(src, 'grey', 'on_green', file=sys.stderr)
    cj = cookies.EzCookieJar()
    cj_kw = dict(ignore_expires=True, ignore_discard=True)
    cj.smart_load(src, **cj_kw)
    give_to_sink(cj.get_netscape_text(**cj_kw), dst)


if __name__ == '__main__':
    main()
