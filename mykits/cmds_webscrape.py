#!/usr/bin/env python3
from mylib.ex.console_app import *
from mylib.sites import misc

apr = ArgumentParserRigger()
an = apr.an


def main():
    apr.parse()
    apr.run()


@apr.sub(aliases=['freevmessuuid'])
def free_ss_site_v2ray_uid():
    print(misc.free_ss_site_vmess_uuid())


if __name__ == '__main__':
    main()
