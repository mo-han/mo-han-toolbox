#!/usr/bin/env python3
import re
from functools import lru_cache

import requests

from ezpykit.allinone import *
from ezpykitext.webclient.browser import EzBrowser
from ezpykitext.webclient.cookies import EzCookieJar
from ezpykitext.webclient.lxml_html import *


class EHentaiGallery:
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
