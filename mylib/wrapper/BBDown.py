#!/usr/bin/env python3
from mylib.ext.console_app import *
from mylib.ext import http_headers

WORK_DIR = '__BBDown__'


class BBDownCLIArgs(CLIArgumentsList):
    def _spec_convert_keyword_to_option_name(self, keyword):
        if keyword in {'tv', 'intl', 'hevc', 'info', 'hs', 'ia', 'mt', }:
            return '-' + keyword
        else:
            return super()._spec_convert_keyword_to_option_name(keyword)

    def set_cookies(self, src):
        cookies = http_headers.get_cookies_dict_from(src)
        sess_data_s = 'SESSDATA'
        self.add(cookie=f'{sess_data_s}={cookies[sess_data_s]}')
