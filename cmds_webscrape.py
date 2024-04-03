#!/usr/bin/env python3
from mylib.ext.console_app import *
from mylib.sites import misc

apr = ArgumentParserWrapper()
an = apr.an


def main():
    apr.parse()
    apr.run()


@apr.sub(aliases=['freevmessuuid'])
def free_ss_site_v2ray_uid():
    print(misc.free_ss_site_vmess_uuid())


@apr.sub(aliases=['xvideos.url.quickies', 'xvq'])
def get_xvideos_quickies_url():
    import lxml.html
    from oldezpykitext.stdlib import os
    import re

    h = lxml.html.fromstring(os.clpb.get_html())
    urls = []
    for e in h.xpath('//div[starts-with(@class, "quickies")]'):
        if 'data-id' not in e.attrib:
            continue
        d = e.attrib
        vid = d['data-id']
        title = e.xpath('.//div[contains(@class, "title")]')[-1].text.lower()
        title = re.sub(r'\W', '_', title)
        title = re.sub('_+', '_', title)
        urls.append(f'https://www.xvideos.com/video{vid}/{title}')
    urls_s = '\n'.join(urls)
    print(urls_s)
    os.clpb.set(urls_s)
    return urls


if __name__ == '__main__':
    main()
