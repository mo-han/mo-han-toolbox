#!/usr/bin/env python3
# encoding=utf8
import os

import requests

from .log import get_logger
from .fsutil import write_json_file
from .tricks import AttributeInflection, width_of_int, Attreebute
from .web_client import HTTPResponseInspection, parse_https_url, make_kwargs_for_lib_requests, DownloadPool

FANBOX_DOMAIN = 'fanbox.cc'
FANBOX_HOMEPAGE = 'https://' + FANBOX_DOMAIN
FANBOX_API_URL = 'https://' + 'api.' + FANBOX_DOMAIN
S_BODY = 'body'

logger = get_logger(__name__)


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


class PostBodyError(Exception):
    pass


class PixivFanboxImage(Attreebute, AttributeInflection):
    def __init__(self, image_dict: dict):
        super().__init__(image_dict)


class PixivFanboxPost(Attreebute, AttributeInflection):
    def __init__(self, post_dict: dict):
        post_body = post_dict['body']
        if post_body is None:
            logger.warning('post body is None: {}'.format(post_dict['id']))
            post_dict['text'] = post_dict['excerpt']
            post_dict['images'] = []
        else:
            try:
                if 'text' in post_body:
                    post_dict['text'] = post_body['text']
                else:
                    post_dict['text'] = '\n'.join([p['text'] for p in post_body['blocks'] if p['type'] == 'p'])
                if 'images' in post_body:
                    post_dict['images'] = [PixivFanboxImage(i) for i in post_body['images']]
                else:
                    post_dict['images'] = []
            except KeyError:
                print(post_dict)
                raise
        super().__init__(post_dict)


class PixivFanboxAPI:
    def __init__(self, **kwargs_for_requests):
        self.api_url = FANBOX_API_URL
        self.kwargs_for_requests = make_kwargs_for_lib_requests(**kwargs_for_requests)
        self.kwargs_for_requests['headers']['Origin'] = FANBOX_HOMEPAGE

    def get(self, url, params=None):
        r = requests.get(url, params=params, **self.kwargs_for_requests)
        logger.debug(r.request.url)
        if r.ok:
            d = r.json()
            if len(d) == 1 and S_BODY in d:
                return d[S_BODY]
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
    return '[{user[name]}] fanbox {creatorId} {user[userId]}'.format(**creator_data)


def download_pixiv_fanbox_post(post_or_id: PixivFanboxPost or dict or str or int, root_dir='.',
                               fanbox_api: PixivFanboxAPI = None,
                               download_pool: DownloadPool = None,
                               retry=-1, **kwargs_for_requests):
    download_pool = download_pool or DownloadPool()
    if isinstance(post_or_id, PixivFanboxPost):
        post = post_or_id
    elif isinstance(post_or_id, dict):
        post = PixivFanboxPost(post_or_id)
    elif isinstance(post_or_id, (str, int)):
        fanbox_api = fanbox_api or PixivFanboxAPI(**kwargs_for_requests)
        post = fanbox_api.get_post_info(post_or_id)
    else:
        raise TypeError(
            "`post_or_id` must be PixivFanboxPost, dict, str, or int, not {}".format(type(post_or_id)))
    creator_folder = pixiv_fanbox_creator_folder(post.__data__)
    creator_id = post.creator_id
    prefix = '{}.'.format(creator_id)
    post_folder = '[{user[name]} {creatorId}] {title} (fanbox {id})'.format(**post.__data__)
    os.makedirs(os.path.join(root_dir, creator_folder, post_folder), exist_ok=True)

    file = prefix + '{}.json'.format(post.id)
    filepath = os.path.join(root_dir, creator_folder, post_folder, file)
    write_json_file(filepath, post.__data__, indent=4)

    url = post.cover_image_url
    if url:
        file = prefix + '{}.cover.{}'.format(post.id, os.path.split(url)[-1])
        filepath = os.path.join(root_dir, creator_folder, post_folder, file)
        download_pool.put_download_in_queue(url, filepath, retry, **kwargs_for_requests)

    n_width = width_of_int(len(post.images))
    n = 0
    for image in post.images:
        n += 1
        file = prefix + '{}.{}.{}.{}'.format(post.id, str(n).zfill(n_width), image.id, image.extension)
        filepath = os.path.join(root_dir, creator_folder, post_folder, file)
        download_pool.put_download_in_queue(image.original_url, filepath, retry, **kwargs_for_requests)

    download_pool.start_queue()
    download_pool.put_end_of_queue()


def download_pixiv_fanbox_creator(creator_id, root_dir='.',
                                  fanbox_api: PixivFanboxAPI = None,
                                  download_pool: DownloadPool = None,
                                  retry=-1, **kwargs_for_requests):
    download_params = {'retry': retry, **kwargs_for_requests}
    fanbox_api = fanbox_api or PixivFanboxAPI(**kwargs_for_requests)
    download_pool = download_pool or DownloadPool()
    creator = fanbox_api.get_creator_info(creator_id)
    creator_id = creator['creatorId']
    prefix = '{}.'.format(creator_id)
    creator['plans'] = fanbox_api.list_sponsor_plan_of_creator(creator_id)
    profile_images = [i for i in creator['profileItems'] if i['type'] == 'image']
    creator_folder = pixiv_fanbox_creator_folder(creator)
    os.makedirs(os.path.join(root_dir, creator_folder), exist_ok=True)

    write_json_file(os.path.join(root_dir, creator_folder, creator_id + '.json'), creator, indent=4)

    url = creator['user']['iconUrl']
    file = prefix + 'icon.' + os.path.split(url)[-1]
    filepath = os.path.join(root_dir, creator_folder, file)
    download_pool.put_download_in_queue(url, filepath, **download_params)

    url = creator['coverImageUrl']
    file = prefix + 'cover.' + os.path.split(url)[-1]
    filepath = os.path.join(root_dir, creator_folder, file)
    download_pool.put_download_in_queue(url, filepath, **download_params)

    n_width = width_of_int(len(profile_images))
    n = 0
    for i in profile_images:
        n += 1
        url = i['imageUrl']
        file = prefix + 'profile{}.{}'.format(str(n).zfill(n_width), os.path.split(url)[-1])
        filepath = os.path.join(root_dir, creator_folder, file)
        download_pool.put_download_in_queue(url, filepath, **download_params)

    for i in creator['plans']:
        url = i['coverImageUrl']
        file = prefix + 'plan{}.{}.{}'.format(i['fee'], i['title'], os.path.split(url)[-1])
        filepath = os.path.join(root_dir, creator_folder, file)
        download_pool.put_download_in_queue(url, filepath, **download_params)

    download_pool.start_queue()
    download_pool.put_end_of_queue()
