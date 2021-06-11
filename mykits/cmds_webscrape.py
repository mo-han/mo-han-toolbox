#!/usr/bin/env python3
from mylib.ex.console_app import *
from mylib.ex.html import *

apr = ArgumentParserRigger()
an = apr.an


def main():
    apr.parse()
    apr.run()


@apr.sub(aliases=['freevmessuid'])
@apr.map(verbose=apr.ro(True))
def free_ss_site_v2ray_uid(verbose=False):
    r = requests.get('https://free-ss.site/')
    for e in lxml.html.fromstring(r.text).cssselect('script'):
        s = e.text
        if s and 'www.kernels.bid' in s:
            for x in re.finditer(REGEX_GUID, s):
                uid = x.group(0)
                if verbose:
                    print(uid)
                return uid


if __name__ == '__main__':
    main()
