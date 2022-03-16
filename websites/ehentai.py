#!/usr/bin/env python3
import re
from functools import lru_cache

import requests

from ezpykit.allinone import *
from ezpykitext.webclient.browser import EzBrowser
from ezpykitext.webclient.cookies import EzCookieJar
from ezpykitext.webclient.lxml_html import *


class EHentaiGallery(T.Generic[T.T]):
    def __init__(self, x):
        self.home = 'https://e-hentai.org'
        if isinstance(x, str):
            gid, token = re.search(r'(\d+)\W+([0-9a-f]{10})', x).groups()
            if 'exhentai' in x:
                self.home = 'https://exhentai.org'
        elif isinstance(x, (tuple, list)):
            gid, token = x
        elif isinstance(x, dict):
            gid = x.get('gid', x.get('id'))
            token = x.get('token', x.get('gtoken'))
        else:
            raise ValueError('invalid e-hentai gallery identity', x)
        gid = int(gid)
        token = str(token)
        if not ezstr.is_hex(token):
            raise ValueError('invalid e-hentai gallery token', token)
        self.gid = gid
        self.token = token
        self.url = f'{self.home}/g/{gid}/{token}'


@lru_cache()
def ensure_gallery(x):
    return x if isinstance(x, EHentaiGallery) else EHentaiGallery(x)


class ExHentaiBrowser(EzBrowser):
    home_url = 'https://exhentai.org'

    def set_cookies(self, source):
        cj = EzCookieJar()
        cj.smart_load(source, ignore_expires=True)
        self.update_cookies(cj.get_dict(), url=self.home_url)

    def visit_gallery(self, gallery):
        g = ensure_gallery(gallery)
        self.visit(g.url)


class EHentaiAPI:
    def __init__(self, ex=False, cookies=None):
        if ex:
            self.home = 'https://exhentai.org'
        else:
            self.home = 'https://e-hentai.org'
        self.session = requests.Session()
        if cookies:
            if isinstance(cookies, dict):
                cookies = cookies
            else:
                cj = EzCookieJar()
                cj.smart_load(cookies, ignore_expires=True)
                cookies = cj.get_dict()
            self.session.cookies.update(cookies)

    @lru_cache()
    def get_gallery_popup_url(self, gallery, action):
        g = ensure_gallery(gallery)
        return f'{self.home}/gallerypopups.php?gid={g.gid}&t={g.token}&act={action}'

    def get_fav(self, gallery):
        url = self.get_gallery_popup_url(gallery, 'addfav')
        r = self.session.get(url)
        r.raise_for_status()
        d = {'favorite': False, 'note': '', }
        ht = html_etree_from(r)
        checked: InputElement = ezlist(ht.cssselect('input[name=favcat][checked]')).first
        if e_is_null(checked):
            return d
        d['favorite'] = int(checked.value)
        note: TextareaElement = ezlist(ht.cssselect('textarea[name=favnote]')).last
        d['note'] = note.text
        return d

    def set_fav(self, gallery, category, note: str = ''):
        if not category == 'favdel':
            if isinstance(category, str):
                category = int(category)
            if not isinstance(category, int):
                raise TypeError('num', 'int', type(category))
            if 9 < category < 0:
                raise ValueError('num', 'range: [0, 9]', category)
        url = self.get_gallery_popup_url(gallery, 'addfav')
        data = dict(favcat=category, favnote=note, apply='Add+to+Favorites', update=1)
        r = self.session.post(url, data=data)
        r.raise_for_status()
        return r

    def del_fav(self, gallery):
        return self.set_fav(gallery, 'favdel')

    @staticmethod
    def post_request_official_api(json_data: dict):
        with ctx_minimum_duration(1):
            r = requests.post('https://api.e-hentai.org/api.php', json=json_data)
            r.raise_for_status()
            return r.json()

    @staticmethod
    def sort_tags_in_metadata(data: dict):
        tags_s = 'tags'
        if tags_s not in data:
            return data
        all_tags = data[tags_s]
        all_tags_d = {}
        for tag in all_tags:
            if ':' in tag:
                k, v = tag.split(':', maxsplit=1)
            else:
                k, v = 'misc', tag
            tag_l = all_tags_d.setdefault(k, [])
            tag_l.append(v)
        data['tags'] = all_tags_d
        return data

    def iget_meta(self, galleries):
        for group in ezlist.ichunks((EHentaiGallery(x) for x in galleries), 25):
            gid_token_group = [[g.gid, g.token] for g in group]
            j = self.post_request_official_api(dict(method='gdata', namespace=1, gidlist=gid_token_group))
            if 'error' in j:
                raise EHentaiError(j['error'])
            for metadata in j['gmetadata']:
                yield self.sort_tags_in_metadata(metadata)


class EHentaiError(Exception):
    errors_d = {
        -1: 'unknown',
        1: 'api invalid json',
        2: 'api invalid key',
        403: 'ip banned',
        404: 'gallery not found',
    }

    def __init__(self, x):
        code, reason, comment = None, None, None
        if isinstance(x, int):
            if x in self.errors_d:
                code = x
            else:
                reason = "undefined error number '{}'".format(x)
        else:
            x = str(x)
            if x.startswith('Your IP address has been temporarily banned'):
                code = 403
                split_by_expire = x.rsplit('The ban expires in ', maxsplit=1)
                if len(split_by_expire) == 2:
                    comment = 'recovering in ' + split_by_expire[-1]
            elif x == 'Key missing, or incorrect key provided.':
                code = 2
            elif x == 'Invalid JSON Request':
                code = 1
            else:
                code = -1
                comment = x
        self.code = code or -1
        self.reason = reason or self.errors_d[self.code]
        if comment:
            self.comment = comment

    def __str__(self):
        if self.comment:
            return 'EHentai Error {}: {}, {}'.format(self.code, self.reason, self.comment)
        else:
            return 'EHentai Error {}: {}'.format(self.code, self.reason)
