#!/usr/bin/env python3

from mylib.ex import http_headers

ROOT_DOMAIN = 'bilibili.com'


class BilibiliSplinterBrowserWrapper:
    def __init__(self, splinter_browser, cookies_dict=None, cookies_source=None):
        b = self.browser = splinter_browser
        b.visit('https://' + ROOT_DOMAIN)
        if cookies_dict:
            self.add_cookies(cookies_dict)
        elif cookies_source:
            self.add_cookies_from(cookies_source)

    def add_cookies_from(self, x):
        self.add_cookies(http_headers.get_cookies_dict_from(x))

    def add_cookies(self, cookies: dict):
        self.browser.cookies.add(cookies)
        for cookie in self.list_cookies():
            cookie['domain'] = ROOT_DOMAIN
            self.add_single_cookie_dict(cookie)
        self.browser.reload()

    def add_single_cookie_dict(self, single_cookie_dict):
        self.browser.driver.add_cookie(single_cookie_dict)

    def get_cookies(self):
        return self.browser.cookies.all()

    def list_cookies(self):
        return self.browser.driver.get_cookies()
