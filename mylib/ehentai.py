#!/usr/bin/env python3
# encoding=utf8
import json
import os
import re
import shutil
from time import sleep

import requests

from .misc import LOG_FMT_MESSAGE_ONLY
from .struct import new_logger, VoidDuck, str_ishex
from .web import cookies_dict_from_file, html_etree
from .os import legal_fs_name

EH_TITLE_REGEX_PATTERN = re.compile(
    r'^'
    r'([\[(].+[)\]])?'
    r'\s*'
    r'([^()\[\]]+(?<!\s))'
    r'\s*'
    r'([\[(].+[)\]])?'
)


def tidy_ehviewer_images(dry_run: bool = False):
    logger = new_logger('ehvimg', fmt=LOG_FMT_MESSAGE_ONLY)
    logmsg_move = '* move {} -> {}'
    logmsg_skip = '# skip {}'
    logmsg_data = '+ /g/{}/{}'
    logmsg_err = '! {}'
    dbf = 'ehdb.json'
    if os.path.isfile(dbf):
        with open(dbf) as fp:
            db = json.load(fp)
            logger.info('@ using DB file: {}'.format(dbf))
    else:
        db = {}
    skipped_gid_l = []
    for f in os.listdir('.'):
        if not os.path.isfile(f):
            continue
        try:
            g = EHentaiGallery(f, logger=logger)
        except ValueError:
            logger.info(logmsg_skip.format(f))
            continue
        gid = g.gid
        if gid in skipped_gid_l:
            logger.info(logmsg_skip.format(f))
            continue
        if gid in db:
            d = db[gid]
        else:
            logger.info(logmsg_data.format(g.gid, g.token))
            d = g.data
            db[gid] = d
            with open(dbf, 'w') as fp:
                json.dump(db, fp)
        title = d['title']
        try:
            core_title_l = EH_TITLE_REGEX_PATTERN.match(title).group(2).split()
        except AttributeError:
            print(logmsg_err.format(title))
            raise
        comic_magazine_title = None
        if core_title_l[0].lower() == 'comic':
            comic_magazine_title_l = []
            for s in core_title_l[1:]:
                if re.match(r'^\d+', s):
                    break
                elif re.match(r'^(?:vol|no\.|#)(.*)$', s.lower()):
                    break
                else:
                    comic_magazine_title_l.append(s)
            if comic_magazine_title_l:
                comic_magazine_title = 'COMIC ' + ' '.join(comic_magazine_title_l)
        try:
            a = d['tags']['artist']
        except KeyError:
            try:
                a = d['tags']['group']
            except KeyError:
                a = ['']
        if len(a) > 3:
            if comic_magazine_title:
                a = comic_magazine_title
            else:
                a = '[]'
        else:
            a = '[{}]'.format(', '.join(a))
        parent, basename = os.path.split(f)
        fn, ext = os.path.splitext(basename)
        fn = str(fn)
        fn = ' '.join(core_title_l[:5]) + ' ' + fn.split()[-1]
        nf = os.path.join(a, legal_fs_name(fn + ext))
        logger.info(logmsg_move.format(f, nf))
        if not dry_run:
            if not os.path.isdir(a):
                os.mkdir(a)
            shutil.move(f, nf)


class EHentaiGallery:
    def __init__(self, gallery_identity, site: str = None, logger=VoidDuck(), wait: float = 10):
        self.logger = logger
        self.wait = wait
        if isinstance(gallery_identity, str):
            gid, token = re.split(r'(\d+)[./\- ]([0-9a-f]{10})', gallery_identity)[1:3]
        elif isinstance(gallery_identity, (tuple, list)):
            gid, token = gallery_identity
            gid, token = str(gid), str(token)
        elif isinstance(gallery_identity, dict):
            gid, token = str(gallery_identity['gid']), str(gallery_identity['token'])
        else:
            raise ValueError("invalid e-hentai gallery identity: '{}'".format(gallery_identity))
        if not gid.isdecimal():
            raise ValueError("invalid e-hentai gallery id: '{}'".format(gid))
        if not str_ishex(token):
            raise ValueError("invalid e-hentai gallery token: '{}'".format(token))
        self._gid = gid
        self._token = token
        if site in ('x', 'ex', 'exhentai'):
            site = 'exhentai'
        else:
            site = 'e-hentai'
        self._site = site
        self._url = 'https://{}.org/g/{}/{}'.format(site, gid, token)
        self.config = {'cookies': {}}
        self._data = {}

    @property
    def gid(self):
        return self._gid

    @property
    def token(self):
        return self._token

    @property
    def url(self):
        return self._url

    @property
    def site(self):
        return self._site

    @site.setter
    def site(self, site: str):
        self._site = site
        self._url = 'https://{}.org/g/{}/{}'.format(site, self._gid, self._token)

    def change_site(self, site: str = None):
        if site:
            self.site = site
        elif self.site == 'e-hentai':
            self.site = 'exhentai'
        elif self.site == 'exhentai':
            self.site = 'e-hentai'
        return self

    def set_cookies(self, cookies: str or dict):
        if isinstance(cookies, str):
            cookies = cookies_dict_from_file(cookies)
        elif isinstance(cookies, dict):
            pass
        else:
            raise TypeError("invalid type cookies: '{}', must be a file path str or a dict.".format(cookies))
        self.config['cookies'] = cookies
        return self

    def gdata(self, wait=None, logger=None):
        j = {'method': 'gdata', 'namespace': 1, 'gidlist': [[self.gid, self.token]]}
        r = requests.post('https://api.e-hentai.org/api.php', json=j)
        gdata = r.json()
        if 'error' in gdata:
            raise EHentaiError(gdata['error'])
        gdata = gdata['gmetadata'][0]
        gdata.update({'token': self.token})
        try:
            tags = gdata['tags']
        except KeyError:
            return gdata
        new_tags = {}
        for tag in tags:
            if ':' in tag:
                tk, tv = tag.split(':', maxsplit=1)
            else:
                tk, tv = 'misc', tag
            if tk not in new_tags:
                new_tags[tk] = []
            new_tags[tk].append(tv)
        gdata.update({'tags': new_tags})
        self._data = gdata
        return gdata

    getdata = gdata

    def get_data_from_page(self, wait=None, logger=None):
        logger = logger or self.logger
        wait = wait or self.wait
        try:
            h = html_etree(self.url, cookies=self.config['cookies'])
        except ConnectionError as e:
            if e.errno == 404:
                raise EHentaiError(e.errno)
            else:
                raise
        finally:
            logger.info('! wait for {}s'.format(wait))
            sleep(wait)
        try:
            gn = h.xpath('//h1[@id="gn"]')[0].text or ''
            gj = h.xpath('//h1[@id="gj"]')[0].text or ''
        except IndexError:
            raise EHentaiError(h.text_content()[:512])
        data = {'title': gn, 'title_jpn': gj, 'token': self.token, 'tags': {}}
        try:
            tags = h.xpath('//div[@id="taglist"]/table')[0]
            for t in tags:
                tk = t[0].text.strip(':')
                tv = [e.text_content().split(' | ', maxsplit=1)[0] for e in t[1]]
                data['tags'][tk] = tv
        except IndexError:
            pass  # no tag
        self._data = data
        return data

    @property
    def data(self):
        if self._data:
            return self._data
        else:
            # return self.get_data_from_page()
            return self.getdata()

    def save_data(self, file_path: str, indent: int = None):
        if os.path.isfile(file_path):
            with open(file_path) as f:
                d = json.load(f)
        else:
            d = {}
        d[self.gid] = self.data
        with open(file_path, 'w') as f:
            json.dump(d, f, indent=indent)


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
