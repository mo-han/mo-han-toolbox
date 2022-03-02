#!/usr/bin/env python3
from mylib.ext.console_app import *
from mylib.sites import iwara

apr = ArgumentParserWrapper()
an = apr.an
an.user = an.general = an.L = an.single_line = ''


@apr.sub()
@apr.arg(an.user)
@apr.true(long_name=an.general)
@apr.true(an.L, an.single_line)
@apr.map(user=an.user, general=an.general, single_line=an.single_line)
def user_video_url(user, general=False, single_line=False):
    s = (' ' if single_line else '\n').join(iwara.iter_all_video_url_of_user(user, ecchi=not general, only_urls=True))
    print(s)
    ostk.clipboard.set(s)


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
