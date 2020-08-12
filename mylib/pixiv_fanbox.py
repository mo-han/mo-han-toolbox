#!/usr/bin/env python3
# encoding=utf8
import requests
from urllib.parse import urlparse

from .web_client import cookies_dict_from_netscape_file, cookies_dict_from_json, cookie_str_from_dict, \
    get_headers_of_cookie, get_headers_of_user_agent, WebRequestFailure, cookies_dict_from_file

FANBOX_DOMAIN = 'fanbox.cc'
FANBOX_HOMEPAGE = 'https://' + FANBOX_DOMAIN
FANBOX_API = 'https://' + 'api.' + FANBOX_DOMAIN
TXT_BODY = 'body'


def get_creator_id_from_url(url: str) -> str or None:
    netloc = urlparse(url).netloc
    if FANBOX_DOMAIN in netloc:
        creator = netloc.split(FANBOX_DOMAIN)[0]
        if creator:
            return creator.rstrip('.')


def get_post_id_from_url(url: str) -> int or None:
    prefix = '/posts/'
    parse = urlparse(url)
    netloc = parse.netloc
    path = parse.path
    if FANBOX_DOMAIN in netloc and path.startswith(prefix):
        post = path[len(prefix):]
        if post:
            return int(post)


class PixivFanboxAPI:
    url = FANBOX_API
    cookies = None
    headers = get_headers_of_user_agent(headers={'Origin': FANBOX_HOMEPAGE})

    def __init__(self, cookies_data: dict or str = None, cookies_filepath: str = None):
        if cookies_data:
            if isinstance(cookies_data, dict):
                self.cookies = cookies_data
            elif isinstance(cookies_data, str):
                self.headers = get_headers_of_cookie(cookies_data, self.headers)
            else:
                raise TypeError('cookies_data', (dict, str))

        if cookies_filepath:
            self.cookies = cookies_dict_from_file(cookies_filepath)

    def get(self, url, param):
        r = requests.get(url, params=param, cookies=self.cookies, headers=self.headers)
        if r.ok:
            d = r.json()
            if len(d) == 1 and TXT_BODY in d:
                return d[TXT_BODY]
            else:
                return d
        else:
            raise WebRequestFailure(r.status_code, r.reason, r.json())

    def get_post_info(self, post_id):
        url = self.url + '/post.info'
        param = {'postId': post_id}
        return self.get(url, param)

    def get_creator_info(self, creator_id):
        url = self.url + '/creator.get'
        param = {'creatorId': creator_id}
        return self.get(url, param)

    def list_post_of_creator(self, creator_id, limit=10) -> list:
        posts = []
        url = self.url + '/post.listCreator'
        param = {'creatorId': creator_id}
        while url:
            if limit is not None:
                param['limit'] = limit
            d = self.get(url, param)
            posts.extend(d['items'])
            url = d['nextUrl']
            if url:
                param = {}
        return posts

    def list_sponsor_plan_of_creator(self, creator_id) -> list:
        url = self.url + '/plan.listCreator'
        param = {'creatorId': creator_id}
        return self.get(url, param)
