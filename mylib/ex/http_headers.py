#!/usr/bin/env python3
import http.cookiejar

import requests.utils

from mylib.easy import *
from mylib.easy import fstk


class Constants:
    netscape_http_cookie_file_header_string = '# Netscape HTTP Cookie File'


class UserAgentExamples:
    """https://www.networkinghowtos.com/howto/common-user-agent-list/"""
    GOOGLE_CHROME_WINDOWS = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    GOOGLE_CHROME_ANDROID = 'Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.82 Mobile Safari/537.36'
    MOZILLA_FIREFOX_WINDOWS = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0'
    MOZILLA_FIREFOX_ANDROID = 'Mozilla/5.0 (Android 11; Mobile) Gecko/88.0 Firefox/88.0'
    MICROSOFT_EDGE = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393'
    APPLE_IPAD = 'Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4'
    APPLE_IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
    GOOGLE_BOT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    BING_BOT = 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)'
    CURL = 'curl/7.35.0'
    WGET = 'Wget'
    LYNX = 'Lynx'


class CURLCookieJar(http.cookiejar.MozillaCookieJar):
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


def ensure_json_list_cookies(json_data: T.JSONType):
    if isinstance(json_data, list):
        cookies = json_data
    elif isinstance(json_data, dict):
        if 'cookies' in json_data:
            cookies = json_data['cookies']
            if not isinstance(cookies, list):
                raise TypeError("data['cookies']", list)
        else:
            raise ValueError("data['cookies'] not exist")
    else:
        raise TypeError('data', T.JSONType)
    return cookies


def json_cookies_to_dict(json_data: T.JSONType = None, json_filepath: str = None, ) -> dict:
    if json_data is not None:
        pass
    elif json_filepath:
        json_data = fstk.read_json_file(json_filepath)
    else:
        raise ValueError('no json source given')
    try:
        cookie_list = ensure_json_list_cookies(json_data)
        return {cookie['name']: cookie['value'] for cookie in cookie_list if isinstance(cookie, dict)}
    except ValueError:
        if isinstance(json_data, dict):
            return json_data


def netscape_cookies_to_dict(cookies_text: str = None, cookies_filepath: str = None, *,
                             ignore_discard=True, ignore_expires=True) -> dict:
    if cookies_text:
        cookies_filepath = io.StringIO(cookies_text)
    if cookies_filepath:
        cj = CURLCookieJar(cookies_filepath)
        cj.load(ignore_discard=ignore_discard, ignore_expires=ignore_expires)
        return requests.utils.dict_from_cookiejar(cj)


def make_cookie_str(cookies: dict):
    return '; '.join([f'{k}={v}' for k, v in cookies.items()])


def parse_cookie_str(s: str):
    s = str_remove_prefix(s, 'Cookie: ')
    return dict([(a, b) for a, b in [i.split('=', maxsplit=1) for i in s.split('; ')]])


def get_cookies_dict_from(x):
    if isinstance(x, str):
        if path_is_file(x):
            if x.endswith('.json'):
                return json_cookies_to_dict(json_filepath=x)
            else:
                return netscape_cookies_to_dict(cookies_filepath=x)
        else:
            return parse_cookie_str(x)
    elif isinstance(x, (list, dict)):
        return json_cookies_to_dict(x)
    else:
        raise TypeError('x', (str, list, dict))


class HTTPHeadersHandler:
    def __init__(self, headers: dict = None):
        self.headers = headers or {}

    @staticmethod
    @functools.lru_cache()
    def _name_to_field(x: str):
        return x.replace('_', '-').title()

    def _set_sth(self, name: str, value):
        value_func = {'Cookie': make_cookie_str}
        field = self._name_to_field(name)
        if field in value_func:
            value = value_func[field](value)
        self.headers[field] = value
        return self

    def _get_sth(self, name: str, *args):
        return self.headers.get(self._name_to_field(name))

    def _del_sth(self, name: str, *args):
        try:
            del self.headers[self._name_to_field(name)]
        except KeyError:
            pass
        return self

    def __getattr__(self, name: str):
        def _set_or_get(value=None):
            """if value given, set item to value; if value is None, get item; if value is ... or False, del item."""
            if value is None:
                func = self._get_sth
            elif value in (..., False):
                func = self._del_sth
            else:
                func = self._set_sth
            return func(name, value)

        _set_or_get.__name__ = name
        self.__dict__[name] = _set_or_get
        return _set_or_get

    def __repr__(self):
        return f'{self.__class__.__name__}({self.headers})'
