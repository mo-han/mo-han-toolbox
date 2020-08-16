#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Library for website operation"""

import http.cookiejar
import json
import os
import re
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures import Future
from io import StringIO
from typing import List

import humanize
import lxml.html
import requests.utils

from .os_util import fs_touch, SubscriptableFileIO
from .tricks import JSONType, EverythingFineNoError, percentage
from .log import get_logger, LOG_FMT_1LEVEL_MESSAGE_ONLY

MAGIC_TXT_NETSCAPE_HTTP_COOKIE_FILE = '# Netscape HTTP Cookie File'
USER_AGENT_FIREFOX_WIN10 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0'

HTMLElementTree = lxml.html.HtmlElement


class HTTPFailure(Exception):
    def __init__(self, response: requests.Response):
        http_ver = {10: '1.0', 11: '1.1'}
        self.ver = http_ver[response.raw.version]
        self.code = int(response.status_code)
        self.desc = str(response.reason)
        self.json = None
        ct = response.headers['content-type']
        if 'json' in ct or 'javascript' in ct:
            try:
                self.json = response.json()
            except json.decoder.JSONDecodeError:
                pass

    def __repr__(self):
        t = '[HTTP/{} {} {}]'.format(self.ver, self.code, self.desc)
        if self.json:
            t += ' JSON={}'.format(self.json)
        return t

    __str__ = __repr__


class HTTPIncomplete(Exception):
    def __init__(self, expect_size: int, recv_size: int):
        self.expect_size = expect_size
        self.recv_size = recv_size


def decode_html_char_ref(x: str) -> str:
    return re.sub(r'&amp;', '&', x, flags=re.I)


def get_html_element_tree(url, **kwargs) -> HTMLElementTree:
    r = requests.get(url, **kwargs)
    if r.ok:
        return lxml.html.document_fromstring(r.text)
    else:
        raise ConnectionError(r.status_code, r.reason)


def convert_cookies_json_to_netscape(json_data_or_filepath: JSONType or str, disable_filepath: bool = False) -> str:
    from .os_util import read_json_file
    if not disable_filepath and os.path.isfile(json_data_or_filepath):
        json_data = read_json_file(json_data_or_filepath)
    else:
        json_data = json_data_or_filepath
    cookies = ensure_json_cookies(json_data)
    tab = '\t'
    false_ = 'FALSE' + tab
    true_ = 'TRUE' + tab
    lines = [MAGIC_TXT_NETSCAPE_HTTP_COOKIE_FILE]
    for c in cookies:
        http_only_prefix = '#HttpOnly_' if c['httpOnly'] else ''
        line = http_only_prefix + c['domain'] + tab
        if c['hostOnly']:
            line += false_
        else:
            line += true_
        line += c['path'] + tab
        if c['secure']:
            line += true_
        else:
            line += false_
        line += '{}\t{}\t{}'.format(c['expirationDate'], c['name'], c['value'])
        lines.append(line)
    return '\n'.join(lines)


def convert_cookies_file_json_to_netscape(src, dst=None) -> str:
    from .os_util import ensure_open_file
    if not os.path.isfile(src):
        raise FileNotFoundError(src)
    dst = dst or src + '.txt'
    with ensure_open_file(dst, 'w') as f:
        f.write(convert_cookies_json_to_netscape(src))
        return dst


def ensure_json_cookies(json_data) -> list:
    if isinstance(json_data, list):
        cookies = json_data
    elif isinstance(json_data, dict):
        if 'cookies' in json_data:
            if isinstance(json_data['cookies'], list):
                cookies = json_data['cookies']
            else:
                raise TypeError("{}['cookies'] is not list".format(json_data))
        else:
            raise TypeError("dict '{}' has no 'cookies'".format(json_data))
    else:
        raise TypeError("'{}' is not list or dict".format(json_data))
    return cookies


def cookies_dict_from_json(json_data_or_filepath: JSONType or str, disable_filepath: bool = False) -> dict:
    from .os_util import read_json_file
    if not disable_filepath and os.path.isfile(json_data_or_filepath):
        json_data = read_json_file(json_data_or_filepath)
    else:
        json_data = json_data_or_filepath
    d = {}
    cookies = ensure_json_cookies(json_data)
    for c in cookies:
        d[c['name']] = c['value']
    return d


class CurlCookieJar(http.cookiejar.MozillaCookieJar):
    """fix issue: MozillaCookieJar ignores '#HttpOnly_' lines"""

    def load(self, filename=None, ignore_discard=False, ignore_expires=False):
        http_only_prefix = '#HttpOnly_'
        http_only_prefix_len = len(http_only_prefix)
        if filename is None:
            if self.filename is not None:
                filename = self.filename
            else:
                # noinspection PyUnresolvedReferences
                raise ValueError(http.cookiejar.MISSING_FILENAME_TEXT)

        with open(filename) as f:
            n = http_only_prefix_len
            lines = [line[n:] if line.startswith(http_only_prefix) else line for line in f.readlines()]

        with StringIO() as f:
            f.writelines(lines)
            f.seek(0)
            # noinspection PyUnresolvedReferences
            self._really_load(f, filename, ignore_discard, ignore_expires)


def cookies_dict_from_netscape_file(filepath: str) -> dict:
    cj = CurlCookieJar(filepath)
    cj.load()
    return requests.utils.dict_from_cookiejar(cj)


def cookies_dict_from_file(filepath: str) -> dict:
    if not os.path.isfile(filepath):
        raise FileNotFoundError(filepath)
    if filepath.endswith('.json'):
        d = cookies_dict_from_json(filepath)
    else:
        d = cookies_dict_from_netscape_file(filepath)
    return d


def cookie_str_from_dict(cookies: dict) -> str:
    cookies_l = ['{}={}'.format(k, v) for k, v in cookies.items()]
    cookie = '; '.join(cookies_l)
    return cookie


def headers_from_user_agent(user_agent: str = None, headers: dict = None) -> dict:
    h = headers or {}
    h['User-Agent'] = user_agent or USER_AGENT_FIREFOX_WIN10
    return h


def headers_from_cookies(cookies_data: dict or str, headers: dict = None) -> dict:
    h = headers or headers_from_user_agent()
    if isinstance(cookies_data, dict):
        cookie = cookie_str_from_dict(cookies_data)
    elif isinstance(cookies_data, str):
        cookie = cookies_data
    else:
        raise TypeError('cookies_data', (dict, str))
    h['Cookie'] = cookie
    return h


def get_phantomjs_splinter(proxy=None, show_image=False, window_size=(1024, 1024)):
    import splinter
    from .os_util import TEMPDIR

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


def get_firefox_splinter(headless=True, proxy: str = None, **kwargs):
    import splinter
    from .os_util import TEMPDIR
    config = {'service_log_path': os.path.join(TEMPDIR, 'geckodriver.log'),
              'headless': headless}
    config.update(kwargs)
    profile_dict = {}
    if proxy:
        from urllib.parse import urlparse
        prefix = 'network.proxy.'
        profile_dict[prefix + 'type'] = 1
        proxy_parse = urlparse(proxy)
        scheme = proxy_parse.scheme
        netloc = proxy_parse.netloc
        try:
            host, port = netloc.split(':')
            port = int(port)
        except ValueError:
            raise ValueError(proxy)
        if scheme in ('http', 'https', ''):
            profile_dict[prefix + 'http'] = host
            profile_dict[prefix + 'http_port'] = port
            profile_dict[prefix + 'https'] = host
            profile_dict[prefix + 'https_port'] = port
        elif scheme.startswith('socks'):
            profile_dict[prefix + 'socks'] = host
            profile_dict[prefix + 'socks_port'] = port
        else:
            raise ValueError(proxy)
    browser = splinter.Browser(driver_name='firefox', profile_preferences=profile_dict, **config)
    return browser


def get_zope_splinter(**kwargs):
    import splinter
    return splinter.Browser(driver_name='zope.testbrowser', **kwargs)


get_browser = {
    'splinter.phantomjs': get_phantomjs_splinter,
}


def human_filesize(bytes_n: int):
    return humanize.naturalsize(bytes_n, binary=True)


class WebDownloadExecutor(ThreadPoolExecutor):
    class DownloadFailure(Exception):
        def __init__(self, url, filepath, latest_exception):
            self.url = url
            self.file = filepath
            self.error = latest_exception

    class Download:
        def __init__(self, r: requests.Response, filepath: str = None):
            if not r.ok:
                raise HTTPFailure(r)
            self.file = filepath or None
            self.code = r.status_code
            self.reason = r.reason
            self.url = r.request.url
            self.data = r.content
            self.size = len(self.data)
            content_length = int(r.headers.get('Content-Length', '-1'))
            if content_length >= 0 and content_length != self.size:
                raise HTTPIncomplete(content_length, self.size)
            if self.code == 206:
                content_range = r.headers['Content-Range']
                start, end, total = [int(s) for s in re.search(r'(\d+)-(\d+)/(\d+)', content_range).groups()]
                self.start = start
                self.stop = end + 1
                if self.stop - self.start != self.size:
                    raise HTTPIncomplete(self.size, self.stop - self.start)
                self.total_size = total
            else:
                self.start = 0
                self.stop = self.size
                self.total_size = self.size

        @property
        def is_206_partial(self):
            return self.code == 206

        @property
        def is_not_206_partial(self):
            return self.code != 206

        @property
        def is_complete_data(self):
            return self.size == self.total_size

        @property
        def is_at_end(self):
            return self.stop >= self.total_size

    def __init__(self, threads: int = 8, name: str = None):
        self.name = name or self.__class__.__name__
        self.logger = get_logger(self.name, fmt=LOG_FMT_1LEVEL_MESSAGE_ONLY)
        super(WebDownloadExecutor, self).__init__(max_workers=threads)

    def submit_download(self, url, filepath, split_size=1024 * 1024, max_retries=3, **kwargs) -> Future:
        return self.submit(self.batch_atomic_download,
                           url, filepath, split_size=split_size, max_retries=max_retries, **kwargs)

    def batch_atomic_download(self, url, filepath, split_size, max_retries, **kwargs) -> List[Future]:
        fs_touch(filepath)
        self.logger.info(
            '+ {} ({}) split={} retry={}'.format(filepath, url, human_filesize(split_size), max_retries))
        first = self.atomic_download(url, filepath, start=0, stop=split_size, max_retries=max_retries, **kwargs)
        total = first.total_size
        if split_size <= 0 or first.is_not_206_partial or first.is_complete_data:
            return []

        start = split_size
        stop = start + split_size
        download_futures = []
        while stop <= total:
            self.logger.info('++ {} ({} - {} / {})'.format(
                filepath, percentage(start / total), percentage(stop / total),
                human_filesize(total)))
            df = self.submit(self.atomic_download,
                             url, filepath, start=start, stop=stop, max_retries=max_retries, **kwargs)
            download_futures.append(df)
            if stop == total:
                break
            start = stop
            stop = start + split_size
            stop = total if stop > total else stop
        else:
            return download_futures

    def atomic_download(self, url, filepath, start, stop, max_retries, **kwargs):
        max_retries = int(max_retries)
        try_cnt = max_retries + 1 if max_retries >= 0 else max_retries
        latest_error = EverythingFineNoError
        while try_cnt:
            try:
                d = self.download(url, filepath, start=start, stop=stop, **kwargs)
                self.write_download_file(d)
                return d
            except Exception as e:
                latest_error = e
                self.logger.warning('! {}'.format(e))
                self.logger.info('++ {} ({} - {}) (retry)'.format(
                    filepath, human_filesize(start), human_filesize(stop)))
                try_cnt -= 1
        else:
            raise self.DownloadFailure(url, filepath, latest_error)

    def download(self, url, filepath, start, stop, **kwargs):
        kwargs = make_kwargs_for_lib_requests(**kwargs)
        if stop:
            kwargs['headers']['Range'] = 'bytes={}-{}'.format(start, stop - 1)
        elif start > 0:
            kwargs['headers']['Range'] = 'bytes={}-'.format(start)
        elif start < 0:
            kwargs['headers']['Range'] = 'bytes={}'.format(start)
        r = requests.get(url, **kwargs)
        return self.Download(r, filepath)

    def write_download_file(self, download: Download):
        total = download.total_size
        file = download.file
        start = download.start
        stop = download.stop
        with SubscriptableFileIO(file) as f:
            if len(f) != total:
                f.truncate(total)
            f[start: stop] = download.data
        self.logger.info(
            '>> {} ({} - {} / {})'.format(
                file, percentage(start / total), percentage(stop / total), human_filesize(total)))


def parse_https_url(url: str, allow_fragments=True):
    from urllib.parse import urlparse
    test_parse = urlparse(url)
    if not test_parse.scheme and not test_parse.netloc:
        url = 'https://' + url
    return urlparse(url, allow_fragments=allow_fragments)


def parse_http_url(url: str, allow_fragments=True):
    from urllib.parse import urlparse
    test_parse = urlparse(url)
    if not test_parse.scheme and not test_parse.netloc:
        url = 'http://' + url
    return urlparse(url, allow_fragments=allow_fragments)


def make_kwargs_for_lib_requests(params=None, cookies=None, headers=None, user_agent=None, proxies=None,
                                 **kwargs):
    user_agent = user_agent or USER_AGENT_FIREFOX_WIN10
    r = {'headers': headers_from_user_agent(user_agent=user_agent, headers=headers)}
    if params:
        r['params'] = params
    if cookies:
        r['cookies'] = cookies
    if proxies:
        r['proxies'] = proxies
    return r
