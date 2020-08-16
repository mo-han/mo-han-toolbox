#!/usr/bin/env python3
# encoding=utf8
import requests

from .web_client import HTTPFailure, parse_https_url, make_kwargs_for_lib_requests
from .tricks import SnakeCaseAttributeInflection

FANBOX_DOMAIN = 'fanbox.cc'
FANBOX_HOMEPAGE = 'https://' + FANBOX_DOMAIN
FANBOX_API_URL = 'https://' + 'api.' + FANBOX_DOMAIN
TXT_BODY = 'body'


def fanbox_creator_id_from_url(url: str) -> str or None:
    netloc = parse_https_url(url).netloc
    if FANBOX_DOMAIN in netloc:
        creator = netloc.split(FANBOX_DOMAIN)[0]
        if creator:
            return creator.rstrip('.')


def fanbox_post_id_from_url(url: str) -> int or None:
    prefix = '/posts/'
    parse = parse_https_url(url)
    netloc = parse.netloc
    path = parse.path
    if FANBOX_DOMAIN in netloc and path.startswith(prefix):
        post = path[len(prefix):]
        if post:
            return int(post)


class PixivFanboxImage(SnakeCaseAttributeInflection):
    def __init__(self, image_dict: dict):
        self.__dict__.update(image_dict)


class PixivFanboxPost(SnakeCaseAttributeInflection):
    def __init__(self, post_dict: dict):
        self.__dict__.update(post_dict)
        self.text = self.__dict__['body']['text']
        self.images = [PixivFanboxImage(i) for i in self.body['images']]


class PixivFanboxAPI:
    def __init__(self, **kwargs_for_requests):
        self.api_url = FANBOX_API_URL
        self.kwargs_for_requests = make_kwargs_for_lib_requests(**kwargs_for_requests)
        self.kwargs_for_requests['headers']['Origin'] = FANBOX_HOMEPAGE

    def get(self, url, params=None):
        r = requests.get(url, params=params, **self.kwargs_for_requests)
        if r.ok:
            d = r.json()
            if len(d) == 1 and TXT_BODY in d:
                return d[TXT_BODY]
            else:
                return d
        else:
            raise HTTPFailure(r)

    def get_post_info(self, post_id):
        url = self.api_url + '/post.info'
        params = {'postId': post_id}
        return PixivFanboxPost(self.get(url, params))

    def get_creator_info(self, creator_id):
        url = self.api_url + '/creator.get'
        params = {'creatorId': creator_id}
        return self.get(url, params)

    def list_post_of_creator(self, creator_id, limit=10) -> list:
        posts = []
        url = self.api_url + '/post.listCreator'
        params = {'creatorId': creator_id, 'limit': limit}
        while url:
            d = self.get(url, params)
            posts.extend(d['items'])
            url = d['nextUrl']
            if url and params:
                params = None
        return [PixivFanboxPost(p) for p in posts]

    def list_sponsor_plan_of_creator(self, creator_id) -> list:
        url = self.api_url + '/plan.listCreator'
        params = {'creatorId': creator_id}
        return self.get(url, params)
