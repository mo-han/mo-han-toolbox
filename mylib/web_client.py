#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Library for website operation"""

import http.cookiejar
import json
import os
import re
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from io import StringIO
from queue import Queue
from time import sleep, time

import colorama
import humanize
import lxml.html
import requests.utils

from .log import get_logger, LOG_FMT_MESSAGE_ONLY
from .os_util import SubscriptableFileIO, fs_touch, write_file_chunk
from .tricks import JSONType, meta_retry_iter, singleton, thread_factory

MAGIC_TXT_NETSCAPE_HTTP_COOKIE_FILE = '# Netscape HTTP Cookie File'
USER_AGENT_FIREFOX_WIN10 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0'

HTMLElementTree = lxml.html.HtmlElement


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
        line += '{}\t{}\t{}'.format(c.get('expirationDate', 0), c['name'], c['value'])
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
    from copy import deepcopy
    h = deepcopy(headers) or {}
    h['User-Agent'] = user_agent or USER_AGENT_FIREFOX_WIN10
    return h


def headers_from_cookies(cookies_data: dict or str, headers: dict = None) -> dict:
    from copy import deepcopy
    h = deepcopy(headers) or headers_from_user_agent()
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


def human_filesize(bytes_n: int, no_space=True):
    s = humanize.naturalsize(bytes_n, binary=True)
    if no_space:
        return s.replace(' ', '')
    else:
        return s


class Download:
    def __init__(self, response: requests.Response, filepath: str = None,
                 content: bytes = None, no_content: bool = False):
        content = b'' if no_content else content or response.content
        if not response.ok:
            raise HTTPResponseInspection(response, content)
        self.id = id(response)
        self.file = filepath or None
        self.code = response.status_code
        self.reason = response.reason
        self.url = response.request.url
        self.data = content
        self.size = len(self.data)
        content_length = int(response.headers.get('Content-Length', '-1'))
        if content_length >= 0 and content_length != self.size:
            raise HTTPIncomplete(content_length, self.size)
        if self.code == 206:
            content_range = response.headers['Content-Range']
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
    def is_complete_data(self):
        return self.size == self.total_size

    @property
    def is_at_end(self):
        return self.stop >= self.total_size


class HTTPResponseInspection(Exception):
    def __init__(self, response: requests.Response, content: bytes = None, no_content: bool = False, size: int = None):
        http_ver = {10: '1.0', 11: '1.1'}
        content = b'' if no_content else content or response.content
        self.version = http_ver[response.raw.version]
        self.code = int(response.status_code)
        self.reason = str(response.reason)
        self.json = None
        self.size = len(content)
        if no_content:
            self.excerpt = None
        elif self.size <= 32:
            self.excerpt = content
        elif self.size <= 4096:
            encoding = response.encoding or response.apparent_encoding
            try:
                text = str(content, encoding=encoding, errors='replace')
            except (LookupError, TypeError):
                text = str(content, errors='replace')
            h: HTMLElementTree = lxml.html.document_fromstring(text)
            self.excerpt = h.body.text_content()
        else:
            self.excerpt = None
        ct = response.headers['content-type']
        if 'json' in ct or 'javascript' in ct:
            try:
                self.json = response.json()
            except json.decoder.JSONDecodeError:
                pass
        if size is not None:
            self.size = size
            self.excerpt = '{} bytes'.format(size)

    def __repr__(self):
        t = 'HTTP/{} {} {}'.format(self.version, self.code, self.reason)
        if self.json:
            t += ', JSON={}'.format(self.json)
        elif self.excerpt:
            t += ', {}'.format(self.excerpt)
        elif self.excerpt is not None:
            t += ', {} bytes'.format(self.size)
        return t

    __str__ = __repr__


class HTTPIncomplete(Exception):
    def __init__(self, expect_size: int, recv_size: int):
        self.expect_size = expect_size
        self.recv_size = recv_size


@singleton
class DownloadPool(ThreadPoolExecutor):
    tmpfile_suffix = '.download'

    def __init__(self, threads_n: int = 5, timeout: int = 30, name: str = None, show_status: bool = True):
        self._max_workers: int = 0
        self.queue = Queue()
        self.timeout = timeout
        self.name = name or self.__class__.__name__
        self.logger = get_logger('.'.join((__name__, self.name)), fmt=LOG_FMT_MESSAGE_ONLY)
        self.recv_size_queue = Queue()
        self.bytes_per_sec = 0
        self.emergency_queue = Queue()
        self.show_status_interval = 2
        self.show_status_enable = show_status
        thread_factory(daemon=True)(self.calc_speed).run()
        thread_factory(daemon=True)(self.show_status).run()
        super().__init__(max_workers=threads_n)

    def queue_pipeline(self):
        self.logger.debug('queue of {} started'.format(self))
        q = self.queue
        while True:
            args = q.get()
            if args is None:
                break
            url, filepath, retry, kwargs_for_requests = args
            self.submit(self.download, url, filepath, retry, **kwargs_for_requests)
            self.logger.debug('submit {}'.format(filepath))
        self.logger.debug('queue of {} stopped'.format(self))

    def show_status(self):
        def color(x):
            left = colorama.Fore.LIGHTGREEN_EX
            right = colorama.Style.RESET_ALL
            return left + str(x) + right

        colorama.init()
        eq = self.emergency_queue
        while True:
            if self.show_status_enable:
                status_msg = '| {} | {} threads | {:>11} |'.format(
                    color(self.name), color(self._max_workers), color(self.speed))
                # status_width = len(status_msg)
                # preamble = shutil.get_terminal_size()[0] - status_width - 1
                # print(' ' * preamble + status_msg, end='\r', file=sys.stderr)
                print(status_msg, end='\r', file=sys.stderr)
            if not eq.empty():
                e = eq.get()
                if isinstance(e, Exception):
                    self.shutdown(wait=False)
                    raise e
            sleep(self.show_status_interval)

    @property
    def speed(self):
        return human_filesize(self.bytes_per_sec, no_space=False) + '/s'

    def calc_speed(self):
        tl = []
        nl = []
        q = self.recv_size_queue
        while True:
            if q.empty():
                sleep(0.1)
                continue
            t, n = q.get()
            tl.append(t)
            nl.append(n)
            try:
                self.bytes_per_sec = sum(nl) // (tl[-1] - tl[0])
            except ZeroDivisionError:
                self.bytes_per_sec = 0
            while time() - tl[0] > self.show_status_interval:
                tl.pop(0)
                nl.pop(0)

    def parse_head(self, url, **kwargs_for_requests):
        head = requests.head(url, **kwargs_for_requests).headers
        split = head.pop('accept-range') == 'bytes'
        size = int(head.pop('content-length', '-1'))
        self.logger.debug('HEAD: split={}, size={}'.format(split, size))

        return {'split': split, 'size': size}

    def request_data(self, url, filepath, start=0, stop=0, **kwargs_for_requests) -> Download:
        # chunk_size = requests.models.CONTENT_CHUNK_SIZE
        chunk_size = 4096 * 1024
        kwargs = make_kwargs_for_lib_requests(**kwargs_for_requests)
        if stop:
            kwargs['headers']['Range'] = 'bytes={}-{}'.format(start, stop - 1)
        elif start > 0:
            kwargs['headers']['Range'] = 'bytes={}-'.format(start)
        elif start < 0:
            kwargs['headers']['Range'] = 'bytes={}'.format(start)
        r = requests.get(url, stream=True, timeout=self.timeout, **kwargs)
        self.logger.debug(HTTPResponseInspection(r, no_content=True))

        content = b''
        stop = 0
        for chunk in r.iter_content(chunk_size=chunk_size):
            self.recv_size_queue.put((time(), len(chunk)))
            start = stop
            stop = start + len(chunk)
            content += chunk
            total = len(content)
            write_file_chunk(filepath, start, stop, chunk, total)
        self.logger.debug(HTTPResponseInspection(r, content=content))
        d = Download(r, filepath, content=content)
        return d

    def write_file(self, dl_obj: Download):
        url = dl_obj.url
        file = dl_obj.file
        start = dl_obj.start
        stop = dl_obj.stop
        size = dl_obj.size
        total = dl_obj.total_size
        with SubscriptableFileIO(file) as f:
            if f.size != total:
                f.truncate(total)
            f[start: stop] = dl_obj.data
            self.logger.debug('w {} ({}) <- {}'.format(file, human_filesize(size), url))

    def download(self, url, filepath, retry, **kwargs_for_requests):
        tmpfile = filepath + self.tmpfile_suffix
        fs_touch(tmpfile)
        for cnt, x in meta_retry_iter(retry)(self.request_data, url, tmpfile, **kwargs_for_requests):
            if isinstance(x, Exception):
                self.logger.warning('! <{}> {}'.format(type(x).__name__, x))
                if cnt:
                    self.logger.info('++ retry ({}) {} <- {}'.format(cnt, filepath, url))
            else:
                dl_obj = x
                break
        else:
            return
        self.write_file(dl_obj)
        os.rename(tmpfile, filepath)
        self.log_file_done(filepath, dl_obj.size)

    def log_file_done(self, filepath, size):
        self.logger.info('* {} ({})'.format(filepath, human_filesize(size)))

    def file_already_exists(self, filepath):
        if os.path.isfile(filepath):
            self.logger.info('# {}'.format(filepath))
            return True
        else:
            return False

    def log_new_download(self, url, filepath, retry):
        self.logger.info('+ {} <- {} (retry={})'.format(filepath, url, retry))

    def submit_download(self, url, filepath, retry, **kwargs_for_requests):
        if self.file_already_exists(filepath):
            return
        future = self.submit(self.download, url, filepath, retry, **kwargs_for_requests)
        self.log_new_download(url, filepath, retry)
        return future

    def put_download_in_queue(self, url, filepath, retry, **kwargs_for_requests):
        if self.file_already_exists(filepath):
            return
        self.queue.put((url, filepath, retry, kwargs_for_requests))
        self.log_new_download(url, filepath, retry)

    def put_end_of_queue(self):
        self.queue.put(None)

    def start_queue(self):
        thread_factory()(self.queue_pipeline).run()


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
    r.update(**kwargs)
    return r
