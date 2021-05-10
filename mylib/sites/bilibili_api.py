#!/usr/bin/env python3
import datetime

from mylib.ex import http_headers
from mylib.easy import *

api_headers_handler: http_headers.HTTPHeadersHandler = http_headers.HTTPHeadersHandler().user_agent(
    http_headers.UserAgentExamples.GOOGLE_CHROME_WINDOWS)


class SortReplyBy:
    time = 0
    popular = 2


class BilibiliWebAPIError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        print(f'[Code {self.code}] {self.message}')


def check_response_json(x: dict):
    code = x['code']
    if code != 0:
        raise BilibiliWebAPIError(code, x['message'])


class SimpleBilibiliWebAPI:
    @functools.lru_cache(maxsize=None)
    def vid2aid(self, x):
        if isinstance(x, int):
            return x
        if isinstance(x, str):
            if re.fullmatch(r'(av|AV)\d+', x):
                return int(x[2:])
            if re.fullmatch(r'BV[\da-zA-Z]{10}', x):
                return self.bvid2aid(x)
            try:
                return int(x)
            except ValueError:
                raise ValueError('invalid video ID')
        raise TypeError('invalid video ID type')

    @functools.lru_cache(maxsize=None)
    def vid2bvid(self, x):
        if isinstance(x, str):
            if re.fullmatch(r'BV[\da-zA-Z]10', x):
                return x
            if re.fullmatch(r'(av|AV)\d+', x):
                return self.aid2bvid(self.vid2aid(x))
            raise ValueError('invalid video ID')
        raise TypeError('invalid video ID type')

    @functools.lru_cache(maxsize=None)
    def aid2bvid(self, aid):
        j = self.web_interface_archive_stat(aid=aid)
        return j['data']['bvid']

    @functools.lru_cache(maxsize=None)
    def bvid2aid(self, bvid):
        j = self.web_interface_archive_stat(bvid=bvid)
        return j['data']['aid']

    @staticmethod
    def request_json(url, **params):
        r = http_headers.requests.get(url, params=params, headers=api_headers_handler.headers)
        j = r.json()
        check_response_json(j)
        return j

    def web_interface_view(self, **params):
        return self.request_json('https://api.bilibili.com/x/web-interface/view', **params)

    def web_interface_archive_stat(self, **params):
        return self.request_json('https://api.bilibili.com/x/web-interface/archive/stat', **params)

    def reply(self, vid, page_num: int = 1, sort=SortReplyBy.popular, simple=True):
        aid = self.vid2aid(vid)
        j = self.request_json('https://api.bilibili.com/x/v2/reply',
                              **dict(oid=aid, type=1, pn=page_num, sort=sort))
        if not simple:
            return j

        def excerpt_single_reply(x: dict):
            return dict(u=(x['member']['uname']), m=(x['content']['message']),
                        t=datetime.datetime.fromtimestamp(x['ctime']).isoformat())

        r = []
        for reply in j['data']['replies']:
            this = excerpt_single_reply(reply)
            children = [excerpt_single_reply(i) for i in reply.get('replies', [])]
            r.append((this, children))
        return r
