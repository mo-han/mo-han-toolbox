#!/usr/bin/env python3
# encoding=utf8
import os

import requests

from .log import get_logger
from .os_util import pushd_context, ensure_open_file, write_json_file
from .web_client import HTTPResponseInspection, parse_https_url, make_kwargs_for_lib_requests, WebDownloadPool
from .tricks import AttributeInflection, width_of_int, Attreebute

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


class PixivFanboxImage(Attreebute, AttributeInflection):
    def __init__(self, image_dict: dict):
        super().__init__(image_dict)


class PixivFanboxPost(Attreebute, AttributeInflection):
    def __init__(self, post_dict: dict):
        post_dict['text'] = post_dict['body']['text']
        post_dict['images'] = [PixivFanboxImage(i) for i in post_dict['body']['images']]
        del post_dict['body']
        super().__init__(post_dict)


class PixivFanboxAPI:
    def __init__(self, **kwargs_for_requests):
        self.logger = get_logger('.'.join((__name__, self.__class__.__name__)))
        self.api_url = FANBOX_API_URL
        self.kwargs_for_requests = make_kwargs_for_lib_requests(**kwargs_for_requests)
        self.kwargs_for_requests['headers']['Origin'] = FANBOX_HOMEPAGE

    def get(self, url, params=None):
        r = requests.get(url, params=params, **self.kwargs_for_requests)
        self.logger.debug(r.request.url)
        if r.ok:
            d = r.json()
            if len(d) == 1 and TXT_BODY in d:
                return d[TXT_BODY]
            else:
                return d
        else:
            raise HTTPResponseInspection(r)

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


def pixiv_fanbox_creator_folder(creator_data: dict):
    return '{creatorId} {user[name]} (pixiv {user[userId]})'.format(**creator_data)


def download_pixiv_fanbox_post(post_or_id: PixivFanboxPost or dict or str or int, root_dir='.',
                               fanbox_api: PixivFanboxAPI = None,
                               download_pool: WebDownloadPool = None,
                               retry=-1, **kwargs_for_requests):
    download_pool = download_pool or WebDownloadPool()
    fanbox_api = fanbox_api or PixivFanboxAPI(**kwargs_for_requests)
    if isinstance(post_or_id, PixivFanboxPost):
        post = post_or_id
    elif isinstance(post_or_id, dict):
        post = PixivFanboxPost(post_or_id)
    elif isinstance(post_or_id, (str, int)):
        post = fanbox_api.get_post_info(post_or_id)
    else:
        raise TypeError('`post_or_id` type: PixivFanboxPost, dict, str, int')
    creator_folder = pixiv_fanbox_creator_folder(post.__data__)
    post_folder = '[{creatorId} ({user[name]})] {title} (fanbox {id})'.format(**post.__data__)
    os.makedirs(os.path.join(root_dir, creator_folder, post_folder), exist_ok=True)

    file = 'post.json'
    filepath = os.path.join(root_dir, creator_folder, post_folder, file)
    write_json_file(filepath, post.__data__, indent=4)

    n_width = width_of_int(len(post.images))
    n = 0
    for image in post.images:
        n += 1
        file = '{}-{}.{}'.format(str(n).zfill(n_width), image.id, image.extension)
        filepath = os.path.join(root_dir, creator_folder, post_folder, file)
        download_pool.queue_download(image.original_url, filepath, retry, **kwargs_for_requests)


def download_pixiv_fanbox_creator(creator_id, root_dir='.',
                                  fanbox_api: PixivFanboxAPI = None,
                                  download_pool: WebDownloadPool = None,
                                  retry=-1, **kwargs_for_requests):
    download_params = {'retry': retry, **kwargs_for_requests}
    fanbox_api = fanbox_api or PixivFanboxAPI(**kwargs_for_requests)
    download_pool = download_pool or WebDownloadPool()
    creator = fanbox_api.get_creator_info(creator_id)
    creator['plans'] = fanbox_api.list_sponsor_plan_of_creator(creator_id)
    profile_images = [i for i in creator['profileItems'] if i['type'] == 'image']
    creator_folder = pixiv_fanbox_creator_folder(creator)
    os.makedirs(os.path.join(root_dir, creator_folder), exist_ok=True)

    write_json_file(os.path.join(root_dir, creator_folder, 'creator.json'), creator, indent=4)
    url = creator['user']['iconUrl']
    file = 'icon-' + os.path.split(url)[-1]
    filepath = os.path.join(root_dir, creator_folder, file)
    download_pool.queue_download(url, filepath, **download_params)

    n_width = width_of_int(len(profile_images))
    n = 0
    for i in profile_images:
        n += 1
        url = i['imageUrl']
        file = 'profile-{}-{}'.format(str(n).zfill(n_width), os.path.split(url)[-1])
        filepath = os.path.join(root_dir, creator_folder, file)
        download_pool.queue_download(url, filepath, **download_params)

    for i in creator['plans']:
        url = i['coverImageUrl']
        file = 'plan-{}-{}'.format(i['fee'], os.path.split(url)[-1])
        filepath = os.path.join(root_dir, creator_folder, file)
        download_pool.queue_download(url, filepath, **download_params)
