#!/usr/bin/env python3
import json
import zipfile
from collections import defaultdict

import requests

import oldezpykit.stdlib.os.common
from mylib.__deprecated__ import get_re_groups
from mylib.easy import *
from mylib.easy import logging
from mylib.ext import fstk
from mylib.ext.tricks import is_hex
from mylib.web_client import cookies_dict_from_netscape_file, get_html_element_tree
from oldezpykit.metautil import VoidDuck
from websites.ehentai import EHentaiError

VARIOUS = '(various)'
UNKNOWN = '(unknown)'
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


def guess_creators_from_ehentai_title(x: str):
    func = functools.partial(get_re_groups, x, )
    creators_pattern_name = 'creators'
    creators_pattern = f'?P<{creators_pattern_name}>'
    _, _, group_dict = ALotCall(
        ACall(func, rf'^(\([^)]+\))\s*\[({creators_pattern}[^]]+)]'),
        ACall(func, rf'^\[(?:pixiv|fanbox|tumblr|twitter)]\s*({creators_pattern}.+)\s*[(\[]', flags=re.I),
        ACall(func, rf'^\W*artist\W*({creators_pattern}\w.*)', flags=re.I),
    ).any_result()
    if creators_pattern_name not in group_dict:
        return []
    creators_str: str = group_dict[creators_pattern_name].strip()
    if '|' in creators_str:
        return [e.strip() for e in creators_str.split('|')]
    else:
        return [creators_str]


def ehviewer_images_catalog(root_dir, *, dry_run: bool = False, db_json_path: str = 'ehdb.json'):
    logger = logging.ez_get_logger('ehvimg', fmt=logging.LOG_FMT_MESSAGE_ONLY)
    logmsg_move = '* move {} -> {}'
    logmsg_skip = '# skip {}'
    logmsg_data = '+ /g/{}/{}'
    logmsg_err = '! {}'

    if os.path.isfile(db_json_path):
        logger.info('@ using DB file: {}'.format(db_json_path))
        db = fstk.read_json_file(db_json_path)
        db = {int(k): v for k, v in db.items()}
    else:
        db = {}

    with oldezpykit.stdlib.os.common.ctx_pushd(root_dir):
        not_found_gid_token = []
        files = []
        for f in next(os.walk('.'))[-1]:
            try:
                g = EHentaiGallery(f, logger=logger)
            except ValueError:
                logger.info(logmsg_skip.format(f))
                continue
            if g.gid not in db and (g.gid, g.token) not in not_found_gid_token:
                not_found_gid_token.append((g.gid, g.token))
                print(logmsg_data.format(g.gid, g.token))
            files.append(f)

        if not_found_gid_token:
            print('... RETRIEVE GALLERY DATA FROM E-HENTAI API ...')
            print('... IT WILL TAKE A LONG TIME ...')
            eh_api = EHentaiAPI()
            for d in eh_api.get_gallery_data(not_found_gid_token):
                db[d['gid']] = d
            fstk.write_json_file(db_json_path, db)

        for f in files:
            g = EHentaiGallery(f, logger=logger)
            d = db[g.gid]
            creators = []
            title = d['title'].strip()
            try:
                core_title = find_core_title(title) or '__INVALID_CORE_TITLE__'
                core_title_l = re.findall(r'[\w]+[\-+\']?[\w]?', core_title)
                if title[:1] + title[-1:] == '[]':
                    creators.append(title[1:-1].strip())
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
                creators = tags['artist']
            elif 'group' in tags:
                creators = tags['group']
            elif 'cosplayer' in tags:
                creators = tags['cosplayer']
            else:
                creators = guess_creators_from_ehentai_title(title)
                if creators:
                    core_title = title
                # todo: clean below code block if guess_creators_from_ehentai_title work well
                # for m in (
                #         re.match(r'^(?:\([^)]+\))\s*\[([^]]+)]', title),
                #         re.match(r'^\[(?:pixiv|fanbox|tumblr|twitter)]\s*(.+)\s*[(\[]', title, flags=re.I),
                #         re.match(r'^\W*artist\W*(\w.*)', title, flags=re.I),
                # ):
                #     if m:
                #         m1 = m.group(1).strip()
                #         if m1:
                #             if '|' in m1:
                #                 creators = [e.strip() for e in m1.split('|')]
                #             else:
                #                 creators = [m1]
                #             core_title = title
                #         break
            if comic_magazine_title:
                folder = comic_magazine_title.replace('COMIC X-E ROS', 'COMIC X-EROS')
            elif 'anthology' in tags.get('misc', []):
                folder = '(anthology)'
            elif creators:
                if len(creators) > 3:
                    folder = VARIOUS
                else:
                    folder = ', '.join(creators)
            else:
                folder = UNKNOWN
            # print(f': {title}')  # DEBUG
            # print(f': {core_title}')  # DEBUG

            sub_folder = fstk.make_path(
                fstk.sanitize_xu200(folder),
                f'{fstk.sanitize_xu200(title)} {g.gid}-{g.token} ehvimg'  # use title instead of core title
            )
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
        elif isinstance(gallery_identity, dict):
            gid, token = gallery_identity['gid'], gallery_identity['token']
        else:
            raise ValueError("invalid e-hentai gallery identity: '{}'".format(gallery_identity))
        # if not gid.isdecimal():
        #     raise ValueError("invalid e-hentai gallery id: '{}'".format(gid))
        gid, token = int(gid), str(token)
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
        gdata = refine_tags_in_dict(gdata)
        self._data = gdata
        return gdata

    getdata = gdata

    def _get_data_from_page___test_only(self, wait=None, logger=None):
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


def ehviewer_dl_folder_rename(folder_path: str, *, db: dict = None, update_db=True):
    db = db or {}
    with oldezpykit.stdlib.os.common.ctx_pushd(folder_path):
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


def parse_hentai_at_home_downloaded_gallery_info(gallery_path, gallery_type=''):
    info = 'galleryinfo.txt'
    desc = 'Downloaded from E-Hentai Galleries by the Hentai@Home Downloader <3'
    if 'd' in gallery_type or os.path.isdir(gallery_path):
        with oldezpykit.stdlib.os.common.ctx_pushd(gallery_path):
            try:
                with open(info, 'tr', encoding='u8') as f:
                    s = f.read()
            except FileNotFoundError:
                return None
    elif 'f' in gallery_type or os.path.isfile(gallery_path):
        with zipfile.ZipFile(gallery_path) as z:
            try:
                with z.open(info) as f:
                    s = f.read().decode('u8')
            except KeyError:
                return None
    else:
        return None
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
    root_dir, name, ext = split_path_dir_base_ext(gallery_path, dir_ext=False)
    try:
        gid_resize = re.search(r' ?\[\d+(-\d{3,4}x)?]$', name).group(0)
    except AttributeError:
        gid_resize = ''
    if gid_resize:
        d['gid_resize'] = gid_resize.strip()
        tail_content = gid_resize.strip(' []')
        if '-' in tail_content:
            gid, resize = tail_content.split('-')
            d['gid'] = int(gid)
            d['resize'] = resize
        else:
            d['gid'] = int(tail_content)
    return d


def refine_tags_in_dict(d: dict):
    try:
        tags = d['tags']
    except KeyError:
        return d
    new_tags = {}
    for tag in tags:
        if ':' in tag:
            tk, tv = tag.split(':', maxsplit=1)
        else:
            tk, tv = 'misc', tag
        if tk not in new_tags:
            new_tags[tk] = []
        new_tags[tk].append(tv)
    d['tags'] = new_tags
    return d


class EHentaiAPI:
    API_URL = 'https://api.e-hentai.org/api.php'
    max_entries = 25
    interval = 1

    def post(self, j):
        r = requests.post(self.API_URL, json=j)
        sleep(self.interval)
        return r.json()

    def split_entries(self, entries):
        entries_n = len(entries)
        groups_n = entries_n // self.max_entries
        if entries_n % self.max_entries:
            groups_n += 1
        if entries_n <= self.max_entries:
            return [list(entries)]
        return [entries[i * self.max_entries:(i + 1) * self.max_entries] for i in range(groups_n)]

    def get_gallery_data(self, gid_token_tuples):
        data_l = []
        for entries in self.split_entries(gid_token_tuples):
            j = self.post({'method': 'gdata', 'namespace': 1, 'gidlist': entries})
            if 'error' in j:
                raise EHentaiError('error')
            data_l.extend([refine_tags_in_dict(d) for d in j['gmetadata']])
        return data_l

    def get_gallery_data_single(self, gid, token):
        return self.post({'method': 'gdata', 'namespace': 1, 'gidlist': [[gid, token]]})
