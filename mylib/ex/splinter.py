#!/usr/bin/env python3
from splinter import *

from mylib.easy import *
from mylib.ex import http_headers


def __ref_sth():
    return Browser


class BrowserWrapper:
    def __init__(self, splinter_browser):
        self._browser = splinter_browser
        self.visit = self.b.visit
        self.quit = self.b.quit

    @property
    def browser(self):
        return self._browser

    @property
    def b(self):
        return self._browser

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.quit()

    def add_cookies(self, cookies, domain=None, reload=False):
        self.browser.cookies.add(cookies)
        for cookie in self.list_cookies():
            cookie['domain'] = domain
            self.add_1cookie_dict(cookie)
        if reload:
            self.browser.reload()

    def add_cookies_from(self, cookies_source, domain=None):
        self.add_cookies(http_headers.get_cookies_dict_from(cookies_source), domain=domain)

    def add_1cookie_dict(self, single_cookie_dict):
        self.browser.driver.add_cookie(single_cookie_dict)

    def get_cookies(self):
        return self.browser.cookies.all()

    def list_cookies(self):
        return self.browser.driver.get_cookies()

    @functools.lru_cache()
    def _method_to_search_element_in_browser(self, prefix, by):
        return getattr(self.browser, f'{prefix}_by_{by}')

    def find(self, wait_time=None, **kw_by_what):
        by, what = kw_by_what.popitem()
        return self._method_to_search_element_in_browser('find', by)(what, wait_time=wait_time)

    def exist(self, wait_time=None, **kw_by_what):
        by, what = kw_by_what.popitem()
        return self._method_to_search_element_in_browser('is_element_present', by)(what, wait_time=wait_time)

    def not_exist(self, wait_time=None, **kw_by_what):
        by, what = kw_by_what.popitem()
        return self._method_to_search_element_in_browser('is_element_not_present', by)(what, wait_time=wait_time)


def make_proxy_settings(address, as_kwargs=False):
    if isinstance(address, str):
        pr = http_headers.ez_parse_netloc(address)
        host = pr.hostname
        port = pr.port
    elif isinstance(address, T.Iterable):
        host, port = address
        port = int(port)
    else:
        raise TypeError('address', (str, T.Iterable))
    profile_preferences = {
        'network.proxy.type': 1,
        'network.proxy.http': host,
        'network.proxy.http_port': port,
        'network.proxy.ssl': host,
        'network.proxy.ssl_port': port,
        'network.proxy.socks': host,
        'network.proxy.socks_port': port,
        'network.proxy.ftp': host,
        'network.proxy.ftp_port': port
    }
    return dict(profile_preferences=profile_preferences) if as_kwargs else profile_preferences
