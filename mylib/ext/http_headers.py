#!/usr/bin/env python3
import http.cookiejar

import requests.utils

from mylib.easy import *
from mylib.easy import fstk


class Constants:
    netscape_http_cookie_file_header_string = '# Netscape HTTP Cookie File'


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
    json_data_var_name = 'json_data'
    if isinstance(json_data, list):
        cookies = json_data
    elif isinstance(json_data, dict):
        if 'cookies' in json_data:
            cookies = json_data['cookies']
            if not isinstance(cookies, list):
                raise TypeError(f"{json_data_var_name}['cookies']", list)
        else:
            raise ValueError(f"{json_data_var_name}['cookies'] not exist")
    else:
        raise TypeError(json_data_var_name, T.JSONType)
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
