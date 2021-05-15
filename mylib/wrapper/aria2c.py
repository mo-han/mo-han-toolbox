#!/usr/bin/env python3

from mylib.ex import http_headers
from mylib.easy import *


class Aria2cCLIArgs(CLIArgumentsList):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.merge_option_nargs = False
        self.add('aria2c')
        self.add(*args, **kwargs)

    def set_cookies(self, cookies: dict):
        return self.set_headers(dict(Cookie=http_headers.make_cookie_str(cookies)))

    def set_headers(self, headers: dict):
        return self.add(header=[f'{k}: {v}' for k, v in headers.items()])


def run_aria2c(*link, cookies: dict = None, headers: dict = None, **options):
    cli_args = Aria2cCLIArgs()
    if cookies:
        cli_args.set_cookies(cookies)
    if headers:
        cli_args.set_headers(headers)
    return subprocess.run(cli_args.add(**options).add(*link))
