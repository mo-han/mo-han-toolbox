#!/usr/bin/env python3
import re

from ezpykit.allinone import *
from ezpykitext.webclient import *

BILIBILI_HOME_PAGE_URL = 'https://www.bilibili.com'
BILIBILI_HEADERS = header.EzHttpHeaders().ua(header.UserAgentExamples.GOOGLE_CHROME_WINDOWS)
BILIBILI_HEADERS.referer(BILIBILI_HOME_PAGE_URL).origin(BILIBILI_HOME_PAGE_URL)
BILIBILI_SHORT_HOME_URL = 'https://b23.tv'


class BilibiliWebAPIError(Exception):
    class Code:
        ACCESS_DENIED = -403

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return f'[Code {self.code}] {self.message}'

    @classmethod
    def check_response(cls, r: requests.Response):
        d = r.json()
        code = d['code']
        if code != 0:
            raise cls(code, d['message'])


def check_response_json(x: dict):
    code = x['code']
    if code != 0:
        raise BilibiliWebAPIError(code, x['message'])


class BilibiliWebAPI:
    class Const:
        REPLY_SORT_RECENT = 0
        REPLY_SORT_POPULAR = 2

    def __init__(self, cookies=None, cache_request: bool = False):
        if cookie.EzCookieJar.is_cookiejar(cookies):
            self.cookies = cookie.EzCookieJar.get_dict(cookies)
        elif cookies:
            self.cookies = cookie.EzCookieJar().smart_load(cookies, ignore_discard=True, ignore_expires=True).get_dict()
        else:
            self.cookies = {}
        self.cache_request = cache_request

    def _request_json(self, url, **params):
        r = requests.get(url, params=params, headers=BILIBILI_HEADERS, cookies=self.cookies)
        j = r.json()
        check_response_json(j)
        try:
            return j['data']
        except KeyError:
            return j['result']

    @functools.lru_cache()
    def _request_json_cached(self, url, **params):
        return self._request_json(url, **params)

    def request_json(self, url: str, **params):
        if self.cache_request:
            return self._request_json_cached(url, **params)
        else:
            return self._request_json(url, **params)

    @functools.lru_cache()
    def clarify_uri(self, uri: str):
        if uri.startswith(BILIBILI_SHORT_HOME_URL):
            r = requests.get(uri)
            uri = r.url
        return uri

    @functools.lru_cache()
    def _parse_vid_dict_cached(self, uri):
        return self._parse_vid_dict(uri)

    def _parse_vid_dict(self, uri):
        if not uri:
            return {}
        if isinstance(uri, int) and uri > 0:
            return dict(aid=uri, bvid=self.aid2bvid(uri))
        if isinstance(uri, dict):
            r = uri
        elif isinstance(uri, str):
            uri = self.clarify_uri(uri)
            r = re.BatchMatchWrapper(
                re.search(r'(av|AV)(?P<aid>\d+)', uri),
                re.search(r'(?P<bvid>BV[\da-zA-Z]{10})', uri),
                re.search(r'(?P<epid>(ep|EP)\d+)', uri),
                re.search(r'(?P<ssid>(ss|SS)\d+)', uri),
            ).first_match().groups_dict('aid', 'bvid', 'epid', 'ssid')
        else:
            r = {}
        if 'aid' not in r and 'bvid' in r:
            r['aid'] = self.bvid2aid(r['bvid'])
        if 'aid' in r:
            r['aid'] = int(r['aid'])
        return r

    def parse_vid_dict(self, uri) -> T.Dict[str, T.Union[int, str]]:
        try:
            hash(uri)
        except TypeError:
            return self._parse_vid_dict(uri)
        else:
            return self._parse_vid_dict_cached(uri)

    def get_tags(self, video_uri, name_only=True, **params):
        d = self.parse_vid_dict(video_uri)
        d.update(params)
        j = self.request_json('https://api.bilibili.com/x/tag/archive/tags', **d)
        if not name_only:
            return j
        return [d['tag_name'] for d in j]

    def get_replies(self, video_uri, page_num: int = 1, sort=Const.REPLY_SORT_POPULAR, text=False, excerpt=True):
        if text:
            excerpt = True
        aid = self.parse_vid_dict(video_uri)['aid']
        j = self.request_json('https://api.bilibili.com/x/v2/reply',
                              oid=aid, pn=page_num, type=1, sort=sort, jsonp='jsonp')
        if not excerpt:
            return j
        r = []
        for reply in j['replies']:
            this = self._excerpt_single_reply(reply)
            children = [self._excerpt_single_reply(i) for i in reply.get('replies') or []]
            r.append((this, children))
        if not text:
            return r
        return self._convert_excerpted_replies_to_text(r, in_lines=text == 'lines')

    @staticmethod
    def _excerpt_single_reply(x: dict):
        return dict(who=(x['member']['uname']), what=(x['content']['message']),
                    when=datetime.datetime.fromtimestamp(x['ctime']).isoformat())

    def _convert_excerpted_replies_to_text(self,
                                           replies: T.List[T.Tuple[T.Dict[str, str], T.List[T.Dict[str, str]]]],
                                           in_lines=False):
        lines = []
        for reply, children in replies:
            lines.extend(self._convert_excerpted_reply_to_lines(reply))
            for child_reply in children:
                lines.extend(self._convert_excerpted_reply_to_lines(child_reply, indent=4))
        if in_lines:
            return lines
        return '\n'.join(lines)

    @staticmethod
    def _convert_excerpted_reply_to_lines(reply, indent=0):
        prefix = ' ' * indent
        return [
            f"{prefix}{reply['who']}",
            f"{prefix}{reply['when'].replace('T', ' ')}",
            *(f'{prefix}{line}' for line in reply["what"].splitlines()),
            prefix,
        ]

    @functools.lru_cache()
    def aid2bvid(self, aid):
        j = self.get_archive_stat_of_web_interface(aid=aid)
        return j['bvid']

    @functools.lru_cache()
    def bvid2aid(self, bvid):
        j = self.get_archive_stat_of_web_interface(bvid=bvid)
        return j['aid']

    # ------------------------------------------------------------------------------------------------------------------

    def get_view_of_web_interface(self, **params):
        return self.request_json('https://api.bilibili.com/x/web-interface/view', **params)

    def get_archive_stat(self, **params):
        return self.request_json('https://api.bilibili.com/archive_stat/stat', **params)

    def get_archive_stat_of_web_interface(self, **params):
        return self.request_json('https://api.bilibili.com/x/web-interface/archive/stat', **params)

    def get_archive_desc_of_web_interface(self, **params):
        return self.request_json('https://api.bilibili.com/x/web-interface/archive/desc', **params)

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
