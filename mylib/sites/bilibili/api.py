#!/usr/bin/env python3
import datetime

from mylib.ext import http_headers
from mylib.easy import *

BILIBILI_HOME_PAGE_URL = 'https://www.bilibili.com'

common_headers = http_headers.HTTPHeadersBuilder().user_agent(
    http_headers.UserAgentExamples.GOOGLE_CHROME_WINDOWS).referer(BILIBILI_HOME_PAGE_URL).origin(
    BILIBILI_HOME_PAGE_URL).headers


class BilibiliWebAPIError(Exception):
    class Code:
        ACCESS_DENIED = -403

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return f'[Code {self.code}] {self.message}'


def check_response_json(x: dict):
    code = x['code']
    if code != 0:
        raise BilibiliWebAPIError(code, x['message'])


class BilibiliWebAPISimple:
    class Const:
        REPLY_SORT_RECENT = 0
        REPLY_SORT_POPULAR = 2

    def __init__(self, cookies: dict = None, cache_request: bool = False):
        self.cookies = cookies
        self.cache_request = cache_request

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
                return self.aid2bvid(int(x[2:]))
            raise ValueError('invalid video ID')
        if isinstance(x, int):
            return self.aid2bvid(x)
        raise TypeError('invalid video ID type')

    @functools.lru_cache(maxsize=None)
    def aid2bvid(self, aid):
        j = self.get_archive_stat_of_web_interface(aid=aid)
        return j['bvid']

    @functools.lru_cache(maxsize=None)
    def bvid2aid(self, bvid):
        j = self.get_archive_stat_of_web_interface(bvid=bvid)
        return j['aid']

    def _request_json(self, url, **params):
        r = http_headers.requests.get(url, params=params, headers=common_headers, cookies=self.cookies)
        j = r.json()
        check_response_json(j)
        try:
            return j['data']
        except KeyError:
            return j['result']

    @functools.lru_cache(maxsize=None)
    def _request_json_cached(self, url, **params):
        return self._request_json(url, **params)

    def request_json(self, url: str, **params):
        if self.cache_request:
            return self._request_json_cached(url, **params)
        else:
            return self._request_json(url, **params)

    def get_view_of_web_interface(self, **params):
        return self.request_json('https://api.bilibili.com/x/web-interface/view', **params)

    def get_archive_stat(self, **params):
        return self.request_json('https://api.bilibili.com/archive_stat/stat', **params)

    def get_archive_stat_of_web_interface(self, **params):
        return self.request_json('https://api.bilibili.com/x/web-interface/archive/stat', **params)

    def get_archive_desc_of_web_interface(self, **params):
        return self.request_json('https://api.bilibili.com/x/web-interface/archive/desc', **params)

    def get_tags(self, simple=True, **params):
        j = self.request_json('https://api.bilibili.com/x/tag/archive/tags', **params)
        if not simple:
            return j
        return [d['tag_name'] for d in j]

    def get_parts(self, **params):
        return self.request_json('https://api.bilibili.com/x/player/pagelist', **params)

    get_page_list = get_parts

    def get_play_url_pgc(self, **params):
        return self.request_json('https://api.bilibili.com/pgc/player/web/playurl', **params)

    def get_play_url_pugc(self, aid, ep_id, cid, **params):
        return self.request_json('https://api.bilibili.com/pugv/player/web/playurl',
                                 avid=aid, ep_id=ep_id, cid=cid, **params)

    def get_play_url_x(self, cid, aid, **params):
        return self.request_json('https://api.bilibili.com/x/player/playurl', cid=cid, avid=aid, **params)

    def get_streams(self, vid, **params):
        # https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/video/videostream_url.md
        ...

    @staticmethod
    def excerpt_single_reply(x: dict):
        return dict(who=(x['member']['uname']), what=(x['content']['message']),
                    when=datetime.datetime.fromtimestamp(x['ctime']).isoformat())

    def get_replies(self, vid, page_num: int = 1, sort=Const.REPLY_SORT_POPULAR, simple=True):
        aid = self.vid2aid(vid)
        j = self.request_json('https://api.bilibili.com/x/v2/reply',
                              **dict(oid=aid, pn=page_num, type=1, sort=sort, jsonp='jsonp'))
        if not simple:
            return j

        r = []
        for reply in j['replies']:
            this = self.excerpt_single_reply(reply)
            children = [self.excerpt_single_reply(i) for i in reply.get('replies') or []]
            r.append((this, children))
        return r

    @staticmethod
    def convert_simple_replies_to_text(simple_replies: T.List[T.Tuple[T.Dict[str, str], T.List[T.Dict[str, str]]]],
                                       in_lines=False):
        lines = []
        for reply, children in simple_replies:
            lines.append(f"[{reply['when'].replace('T', ' ')}] {reply['who']}")
            lines.extend(f'{line}' for line in reply["what"].splitlines())
            lines.append('')
            for child_reply in children:
                lines.append(f"    [{child_reply['when'].replace('T', ' ')}] {child_reply['who']}")
                lines.extend(f"    {line}" for line in child_reply['what'].splitlines())
                lines.append('')
        if in_lines:
            return lines
        return '\n'.join(lines)

    rpl2txt = convert_simple_replies_to_text
