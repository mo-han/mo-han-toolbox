#!/usr/bin/env python3
from splinter import *
from mylib.ex import http_headers


def __ref_sth():
    return Browser


class BrowserWrapper:
    def __init__(self, splinter_browser):
        self.browser = splinter_browser

    def add_cookies(self, cookies, domain=None):
        self.browser.cookies.add(cookies)
        for cookie in self.list_cookies():
            cookie['domain'] = domain
            self.add_1cookie_dict(cookie)
        self.browser.reload()

    def add_cookies_from(self, cookies_source, domain=None):
        self.add_cookies(http_headers.get_cookies_dict_from(cookies_source), domain=domain)

    def add_1cookie_dict(self, single_cookie_dict):
        self.browser.driver.add_cookie(single_cookie_dict)

    def get_cookies(self):
        return self.browser.cookies.all()

    def list_cookies(self):
        return self.browser.driver.get_cookies()
