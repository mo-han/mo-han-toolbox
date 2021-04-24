#!/usr/bin/env python3
import http.cookiejar

import requests.utils

from mylib.easy import *
from mylib.easy import fstk


class Constants:
    netscape_http_cookie_file_header_string = '# Netscape HTTP Cookie File'


class UserAgentExamples:
    """https://www.networkinghowtos.com/howto/common-user-agent-list/"""
    google_chrome_windows = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    google_chrome_android = 'Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.82 Mobile Safari/537.36'
    mozilla_firefox_windows = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0'
    mozilla_firefox_android = 'Mozilla/5.0 (Android 11; Mobile) Gecko/88.0 Firefox/88.0'
    microsoft_edge = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393'
    apple_ipad = 'Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4'
    apple_iphone = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
    google_bot = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    bing_bot = 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)'
    curl = 'curl/7.35.0'
    wget = 'Wget'
    lynx = 'Lynx'


class CurlCookieJar(http.cookiejar.MozillaCookieJar):
    """fix issue: MozillaCookieJar ignores '#HttpOnly_' lines"""
    filename_types = (str, io.StringIO)

    def __init__(self, filename: T.Union[filename_types] = None, delayload=False, policy=None):
        """
        Cookies are NOT loaded from the named file until either the .load() or
        .revert() method is called.

        """
        http.cookiejar.CookieJar.__init__(self, policy)
        if filename is not None:
            if not isinstance(filename, self.filename_types):
                raise TypeError('filename', self.filename_types)
        self.filename = filename
        self.delayload = bool(delayload)

    def load(self, filename=None, ignore_discard=False, ignore_expires=False):
        http_only_prefix = '#HttpOnly_'

        if filename is None:
            if self.filename is not None:
                filename = self.filename
            else:
                # noinspection PyUnresolvedReferences
                raise ValueError(http.cookiejar.MISSING_FILENAME_TEXT)

        if isinstance(filename, io.StringIO):
            lines = [str_remove_prefix(line, http_only_prefix) for line in filename.readlines()]
        else:
            with open(filename) as fd:
                lines = [str_remove_prefix(line, http_only_prefix) for line in fd.readlines()]
        # print(''.join(lines))  # DEBUG

        with io.StringIO() as fd:
            fd.writelines(lines)
            fd.seek(0)
            # noinspection PyUnresolvedReferences
            self._really_load(fd, filename, ignore_discard, ignore_expires)


def ensure_json_cookies(data: T.JSONType) -> T.List[dict]:
    if isinstance(data, list):
        cookies = data
    elif isinstance(data, dict):
        if 'cookies' in data:
            if isinstance(data['cookies'], list):
                cookies = data['cookies']
            else:
                raise ValueError("data['cookies'] is not list")
        else:
            raise ValueError("data['cookies'] not exist")
    else:
        raise TypeError('data', T.JSONType)
    return cookies


def json_cookies_to_dict(json_data: T.JSONType = None, json_filepath: str = None, ) -> dict:
    if json_data:
        pass
    elif json_filepath:
        json_data = fstk.read_json_file(json_filepath)
    else:
        raise ValueError('no json source given')
    d = {}
    cookies = ensure_json_cookies(json_data)
    for cookie in cookies:
        d[cookie['name']] = cookie['value']
    return d


def netscape_cookies_to_dict(cookies_text: str = None, cookies_filepath: str = None, *,
                             ignore_discard=True, ignore_expires=True) -> dict:
    if cookies_text:
        cookies_filepath = io.StringIO(cookies_text)
    if cookies_filepath:
        cj = CurlCookieJar(cookies_filepath)
        cj.load(ignore_discard=ignore_discard, ignore_expires=ignore_expires)
        return requests.utils.dict_from_cookiejar(cj)


def make_cookie_str(cookies: dict) -> str:
    return '; '.join([f'{k}={v}' for k, v in cookies.items()])


class HTTPHeadersHandler:
    def __init__(self, headers: dict):
        self.headers = headers

    def _set_sth(self, key: str, value):
        self.headers[key.title()] = value
        return self

    def __getattr__(self, item: str):
        if item.startswith('set_'):
            key = str_remove_prefix(item, 'set_').replace('_', '-')
            return functools.partial(self._set_sth, key)
        return getattr(self.headers, item)

    def set_cookie(self, cookies: dict):
        self.headers['Cookie'] = make_cookie_str(cookies)
        return self
