#!/usr/bin/env python3
import re

from oldezpykit.allinone import *
from oldezpykitext.webclient import *

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
        self.cookies = {}
        self.set_cookies(cookies)
        self.cache_request = cache_request

    def set_cookies(self, cookies):
        if cookie.EzCookieJar.is_cookiejar(cookies):
            self.cookies = cookie.EzCookieJar.get_dict(cookies)
        elif cookies:
            self.cookies = cookie.EzCookieJar().smart_load(cookies, ignore_discard=True, ignore_expires=True).get_dict()
        return self

    def _request_json(self, url, **params) -> dict:
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

    def _parse_vid_dict(self, video_source):
        if not video_source:
            return {}
        if isinstance(video_source, int) and video_source > 0:
            return dict(aid=video_source, bvid=self.aid2bvid(video_source))
        if isinstance(video_source, dict):
            r = video_source
        elif isinstance(video_source, str):
            video_source = self.clarify_uri(video_source)
            r = re.BatchMatchWrapper(
                re.search(r'(av|AV)(?P<aid>\d+)', video_source),
                re.search(r'(?P<bvid>BV[\da-zA-Z]{10})', video_source),
                re.search(r'(ep|EP)(?P<ep_id>\d+)', video_source),
                re.search(r'(ss|SS)(?P<season_id>\d+)', video_source),
            ).first_match().pick_existing_group_dict('aid', 'bvid', 'ep_id', 'season_id')
            c = TypeConverter(int)
            r = {k: c.convert(v) for k, v in r.items()}
        else:
            r = {}
        if 'aid' not in r:
            if 'bvid' in r:
                r['aid'] = self.bvid2aid(r['bvid'])
            if 'ep_id' in r:
                r['aid'] = self.get_episodes_info_web_season(**r)['this_episode']['aid']
        return r

    def parse_vid_dict(self, video_source) -> T.Dict[str, T.Union[int, str]]:
        try:
            hash(video_source)
        except TypeError:
            return self._parse_vid_dict(video_source)
        else:
            return self._parse_vid_dict_cached(video_source)

    def get_tags(self, video_source, name_only=True, **params):
        d = self.parse_vid_dict(video_source)
        d.update(params)
        j = self.request_json('https://api.bilibili.com/x/tag/archive/tags', **d)
        if not name_only:
            return j
        return [d['tag_name'] for d in j]

    def get_replies(self, video_source, page_num: int = 1, sort=Const.REPLY_SORT_POPULAR, text=False, excerpt=True):
        if text:
            excerpt = True
        aid = self.parse_vid_dict(video_source)['aid']
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

    def get_episodes_info_web_season(self, **params):
        """剧集 bangumi web端 epid ssid
        :param params: ep_id, season_id
        """
        r = self.request_json('https://api.bilibili.com/pgc/view/web/season', **params)
        if 'ep_id' in params:
            for e in r['episodes']:
                if e['id'] == params['ep_id']:
                    r['this_episode'] = e
                    break
        return r

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
