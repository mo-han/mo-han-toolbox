#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Library for website operation"""

import os
import requests
from lxml import html
import http.cookiejar

USER_AGENT_FIREFOX_WIN10 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0'

_headers = {
    'user-agent': USER_AGENT_FIREFOX_WIN10,
}


def html_etree(url, **kwargs) -> html.HtmlElement:
    r = requests.get(url, headers=_headers, **kwargs)
    if r.ok:
        return html.document_fromstring(r.text)
    else:
        raise ConnectionError(r.status_code, r.reason)


def cookies_dict_from_file(file_path: str) -> dict:
    cj = http.cookiejar.MozillaCookieJar(file_path)
    cj.load()
    return requests.utils.dict_from_cookiejar(cj)


def cookie_str_from_dict(cookies: dict) -> str:
    cookies_l = ['{}={}'.format(k, v) for k, v in cookies.items()]
    cookie = '; '.join(cookies_l)
    return cookie


class DownloadFailure(Exception):
    pass


def get_phantomjs_splinter(proxy=None, show_image=False, window_size=(1024, 1024)):
    import splinter
    from mylib.osutil import TEMPDIR

    extra_argv = ['--webdriver-loglevel=WARN']
    if proxy:
        extra_argv.append('--proxy={}'.format(proxy))
    if not show_image:
        extra_argv.append('--load-images=no')

    b = splinter.Browser(
        'phantomjs',
        service_log_path=os.path.join(TEMPDIR, 'ghostdriver.log'),
        user_agent=USER_AGENT_FIREFOX_WIN10,
        service_args=extra_argv,
    )
    b.driver.set_window_size(*window_size)
    return b


def try_dl_file(url: str, max_retries: int = 3) -> tuple:
    pass


get_browser = {
    'splinter.phantomjs': get_phantomjs_splinter
}
