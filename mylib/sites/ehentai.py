#!/usr/bin/env python3
# encoding=utf8
import json
import zipfile
from collections import defaultdict

import requests

from mylib import fstk
from mylib.ez import *
from mylib.ez import log_kit
from mylib.tricks_lite import VoidDuck, is_hex
from mylib.web_client import cookies_dict_from_netscape_file, get_html_element_tree

EH_TITLE_REGEX_PATTERN = re.compile(
    r'^'
    r'([\[(].+[)\]])?'
    r'\s*'
    r'([^()\[\]]+(?<!\s))'
    r'\s*'
    r'([\[(].+[)\]])?'
)

non_bracket = r'[^\[\]()]'


def find_core_title(title: str):
    # split_by_right_l = re.split(r'[])]', title)
    # for s in split_by_right_l:
    #     print(s)  # DEBUG
    #     if re.match(r'\s*[\[(]', s):
    #         continue
    #     elif re.search(r'\S.*[\[(]', s):
    #         return re.split(r'[\[(]', s)[0].strip()
    t = title
    t = re.sub(rf'(\[{non_bracket}+\({non_bracket}+\))({non_bracket}+)', r'\1\]\2', t)  # missing `]`
    t = re.sub(r'^\s*\([^)]+\)(.+)', r'\1', t)
    t = re.sub(r'^\s*\[[^]]+](.+)', r'\1', t)
    t = re.sub(r'^\s*([^[]+)\[.+]', r'\1', t)
    return t.strip()


def ehviewer_images_catalog(dry_run: bool = False, db_json_path: str = 'ehdb.json'):
    logger = log_kit.get_logger('ehvimg', fmt=log_kit.LOG_FMT_MESSAGE_ONLY)
    logmsg_move = '* move {} -> {}'
    logmsg_skip = '# skip {}'
    logmsg_data = '+ /g/{}/{}'
    logmsg_err = '! {}'

    if os.path.isfile(db_json_path):
        logger.info('@ using DB file: {}'.format(db_json_path))
        db = fstk.read_json_file(db_json_path)
    else:
        db = {}
    skipped_gid_l = []

    for f in os.listdir('..'):
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
            fstk.write_json_file(db_json_path, db, indent=4)
            sleep(1)

        artist_l = []
        title = d['title'].strip()
        try:
            core_title = find_core_title(title) or '__INVALID_CORE_TITLE__'
            core_title_l = re.findall(r'[\w]+[\-+\']?[\w]?', core_title)
            if title[:1] + title[-1:] == '[]':
                artist_l.append(title[1:-1].strip())
        except AttributeError:
            print(logmsg_err.format(title))
            raise
        comic_magazine_title = None
        if core_title_l and core_title_l[0].lower() == 'comic':
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

        tags = d['tags']
        if 'artist' in tags:
            artist_l = tags['artist']
        elif 'group' in tags:
            artist_l = tags['group']
        else:
            for m in (
                    re.match(r'^(?:\([^)]+\))\s*\[([^]]+)]', title),
                    re.match(r'^\[(?:pixiv|fanbox|tumblr|twitter)]\s*(.+)\s*[(\[]', title, flags=re.I),
                    re.match(r'^\W*artist\W*(\w.*)', title, flags=re.I),
            ):
                if m:
                    m1 = m.group(1).strip()
                    if m1:
                        if '|' in m1:
                            artist_l = [e.strip() for e in m1.split('|')]
                        else:
                            artist_l = [m1]
                        core_title = title
                    break
        if len(artist_l) > 3:
            if comic_magazine_title:
                folder = comic_magazine_title
            else:
                folder = '[...]'
        else:
            folder = '[{}]'.format(', '.join(artist_l))
        # print(f': {title}')  # DEBUG
        # print(f': {core_title}')  # DEBUG

        sub_folder = fstk.make_path(fstk.sanitize_xu200(folder), f'{fstk.sanitize_xu200(core_title)} {g.gid}-{g.token}')
        parent, basename = os.path.split(f)
        no_ext, ext = os.path.splitext(basename)
        no_ext = fstk.sanitize_xu240(no_ext.split()[-1])
        new_path = fstk.make_path(sub_folder, no_ext + ext)
        logger.info(logmsg_move.format(f, new_path))
        if not dry_run:
            os.makedirs(sub_folder, exist_ok=True)
            shutil.move(f, new_path)


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
        if not is_hex(token):
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
            cookies = cookies_dict_from_netscape_file(cookies)
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
            h = get_html_element_tree(self.url, cookies=self.config['cookies'])
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


def ehviewer_dl_folder_rename(folder_path: str, *, db: dict = None, update_db=False):
    db = db or {}
    with fstk.ctx_pushd(folder_path):
        with open('.ehviewer') as info_file:
            info_lines = info_file.readlines()
    gid = info_lines[2].strip()
    token = info_lines[3].strip()
    d = db.get(gid) or EHentaiGallery(f'{gid}/{token}').data
    if update_db:
        db[gid] = d
    title = d.get('title') or d.get('original title')
    if not title:
        return
    title = fstk.sanitize(title)
    return fstk.x_rename(folder_path, title)


def parse_hath_dl_gallery_info(gallery):
    info = 'galleryinfo.txt'
    desc = 'Downloaded from E-Hentai Galleries by the Hentai@Home Downloader <3'
    if os.path.isdir(gallery):
        with fstk.ctx_pushd(gallery):
            if not os.path.isfile(info):
                raise FileNotFoundError(fstk.make_path(gallery, info))
            with open(info, 'tr', encoding='u8') as f:
                s = f.read()
    elif os.path.isfile(gallery):
        with zipfile.ZipFile(gallery) as z:
            try:
                with z.open(info) as f:
                    s = f.read().decode('u8')
            except KeyError:
                raise FileNotFoundError(f'{gallery}::{info}')
    else:
        raise FileNotFoundError(gallery)
    s = str_remove_suffix(s.strip(), desc)
    d = {}
    try:
        meta, cmt = s.split("Uploader's Comments:", maxsplit=1)
    except ValueError:
        meta, cmt = s, None
    # print(meta)
    # print(cmt)
    title_s, upload_time_s, uploader_s, download_time_s, tags_s = meta.strip().splitlines()
    d['title'] = str_remove_prefix(title_s, 'Title:').strip()
    d['upload time'] = str_remove_prefix(upload_time_s, 'Upload Time:').strip()
    d['uploader'] = str_remove_prefix(uploader_s, 'Uploaded By:').strip()
    d['download time'] = str_remove_prefix(download_time_s, 'Downloaded:').strip()
    tags = defaultdict(list)
    for e in str_remove_prefix(tags_s, 'Tags:').strip().split(', '):
        if ':' in e:
            tag_name, tag_value = e.split(':', maxsplit=1)
            tags[tag_name].append(tag_value)
        else:
            tags['misc'].append(e)
    d['tags'] = tags
    d['uploader comments'] = cmt.strip() if cmt is not None else None
    return d
