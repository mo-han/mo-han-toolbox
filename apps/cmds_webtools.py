#!/usr/bin/env python3
from ezpykitext.appkit import *
from ezpykitext.extlib.termcolor import *
from ezpykitext.webclient import *

apr = argparse.ArgumentParserWrapper()


def main():
    logging.init_root(fmt=logging.FMT_MESSAGE_ONLY)
    apr.parse()
    apr.run()


@apr.sub(aliases=['get-cookies', 'getck'])
@apr.opt('s', 'src')
@apr.opt('d', 'dst')
@apr.true('v', 'verbose')
@apr.map('src', 'dst', verbose='verbose')
def get_netscape_cookies(src, dst, verbose=False):
    """get netscape format cookies, from src to dst"""
    if verbose:
        logging.set_root_level('INFO')
    lg = logging.get_logger(__name__, get_netscape_cookies.__name__)
    src = get_from_source(src)
    lg.info(colored(str(src), 'grey', 'on_white', ['bold']))
    cj = cookies.EzCookieJar()
    cj_kw = dict(ignore_expires=True, ignore_discard=True)
    cj.smart_load(src, **cj_kw)
    r = cj.get_netscape_text(**cj_kw)
    lg.info(colored(str(r), 'grey', None, ['bold']))
    give_to_sink(r, dst)


if __name__ == '__main__':
    main()
