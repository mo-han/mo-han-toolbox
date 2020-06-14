#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import shutil
from glob import glob
from http.cookiejar import MozillaCookieJar

import requests
from lxml import html

from . import you_get_bilibili
from .misc import safe_print, safe_basename
from .video import concat_videos, merge_m4s
from .web import cookie_string_from_dict, cookies_dict_from_file


class BilibiliError(RuntimeError):
    pass


def tmp(avid, cid):
    param = {'avid': avid, 'cid': cid, 'type': '', 'otype': 'json', 'fnver': 0, 'fnval': 16}
    api_url = 'https://api.bilibili.com/x/player/playurl'
    r = requests.get(api_url, param)
    return r.json()


def download_bilibili_video(url, cookies: str or dict = None, part_list: list = None, playlist: bool = None,
                            info: bool = False, output: str = '.'):
    bv = BilibiliVideo(cookies=cookies)
    if info:
        dl_kwargs = {'info_only': True}
    else:
        dl_kwargs = {'output_dir': output, 'merge': True, 'caption': True}
    if playlist:
        bv.download_playlist_by_url(url, **dl_kwargs)
    else:
        if part_list:
            bv.url = url
            vid = bv.get_vid()
            for p in part_list:
                url = 'https://www.bilibili.com/video/{}?p={}'.format(vid, p)
                bv.download_by_url(url, **dl_kwargs)


class BilibiliVideo(you_get_bilibili.Bilibili):
    def __init__(self, *args, cookies: str or dict = None, qn_max=116):
        super(BilibiliVideo, self).__init__(*args)
        self.cookie = None
        if cookies:
            self.set_cookie(cookies)

    def set_cookie(self, cookies: str or dict):
        if isinstance(cookies, dict):
            c = cookie_string_from_dict(cookies)
        elif isinstance(cookies, str):
            if os.path.isfile(cookies):
                c = cookie_string_from_dict(cookies_dict_from_file(cookies))
            else:
                c = cookies
        else:
            raise TypeError("'{}' is not cookies file path str or joined cookie str or dict".format(cookies))
        self.cookie = c

    def bilibili_headers(self, referer=None, cookie=None):
        if not cookie:
            cookie = self.cookie
        headers = super(BilibiliVideo, self).bilibili_headers(referer=referer, cookie=cookie)
        return headers

    def get_vid(self):
        url = self.url
        for m in [re.search(r'/(av\d+)', url), re.search(r'/(bv\w+)', url, flags=re.I)]:
            if m:
                vid = m.group(1)
                if vid.startswith('bv'):
                    vid = 'BV' + vid[2:]
                break
        else:
            vid = None
        return vid

    def get_uploader(self):
        url = self.url
        headers = self.bilibili_headers()
        r = requests.get(url, headers=headers)
        h = html.document_fromstring(r.text)
        return h.xpath('//meta[@name="author"]')[0].attrib['content']


def jijidown_rename_alpha(path: str, part_num=True):
    rename = os.rename
    isfile = os.path.isfile
    isdir = os.path.isdir
    basename = os.path.basename
    dirname = os.path.dirname
    path_join = os.path.join

    def _ren_file(filepath):
        name = basename(filepath)
        parent = dirname(filepath)
        print('{}:'.format(parent))
        new_name = re.sub(r'\.[Ff]lv\.mp4$', '.mp4', name)
        new_name = re.sub(r'^(\d+\.)?(.*?)\(Av(\d+).*?\)', r'\1 \2 [av\3]', new_name)
        if not part_num:
            new_name = re.sub(r'^\d+\.', '', new_name)
        # if new_name[-5:] == '].ass' and new_name[-8:-5] != '+弹幕':
        #     new_name = new_name[:-5] + '+弹幕].ass'
        # elif new_name[-5:] == '].xml' and new_name[-8:-5] != '+弹幕':
        #     new_name = new_name[:-5] + '+弹幕].xml'
        if new_name[-4:] == '.ass':
            new_name = new_name[:-4] + '.bilibili-danmaku-ass'
        elif new_name[-6:] == 'lv.mp4':
            new_name = new_name[:-8] + '.mp4'
        new_name = new_name.strip()
        print('{} -> {}'.format(name, new_name))
        new_filepath = path_join(parent, new_name)
        rename(filepath, new_filepath)

    if isfile(path):
        _ren_file(path)
    elif isdir(path):
        for i in [path_join(path, f) for f in os.listdir(path)]:
            _ren_file(i)
    else:
        print('Not exist: {}'.format(path))


class BilibiliAppCacheEntry:
    def __init__(self, vid_dir_path, cookies_file_path: str = None):
        if cookies_file_path:
            self.cookies = requests.utils.dict_from_cookiejar(MozillaCookieJar(cookies_file_path))
        else:
            self.cookies = None
        self.folder = vid_dir_path
        self.work_dir, self.id = os.path.split(os.path.realpath(vid_dir_path))
        self.part_list = os.listdir(vid_dir_path)
        self.part_sum = len(self.part_list)
        self._current_part = None
        self._current_meta = None

    def get_uploader(self):
        url = 'https://www.bilibili.com/video/av{}/'.format(self.id)
        param = {}
        if self.cookies:
            param['cookies'] = self.cookies
        r = requests.get(url, **param)
        h = html.document_fromstring(r.text)
        return h.xpath('//meta[@name="author"]')[0].attrib['content']

    # def get_uploader(self):
    #     url = 'https://www.bilibili.com/video/av{}/'.format(self.id)
    #     self.browser.visit(url)
    #     meta_author = self.browser.find_by_xpath('//meta[@name="author"]').first.outer_html
    #     author = meta_author.split('content="')[-1].split('"')[0]
    #     if author:
    #         return author
    #     else:
    #         # raise BilibiliError('No author found.')
    #         return ''

    def extract_part(self):
        print('+ {}'.format(self.folder))
        for part in self.part_list:
            self._current_part = part
            print('  + {}'.format(part), end=': ')
            try:
                self._current_meta = meta = json.load(
                    open(os.path.join(self.folder, part, 'entry.json'), encoding='utf8'))
            except FileNotFoundError:
                # os.remove(os.path.join(self.folder, part))
                print('    NO JSON META FOUND')
                continue
            if 'page_data' in meta:
                self.extract_vupload()
            elif 'ep' in meta:
                self.extract_bangumi()

    def extract_vupload(self):
        title = safe_basename(self._current_meta['title'])
        file_list = glob(os.path.join(self.folder, self._current_part, self._current_meta['type_tag'], '*'))
        ext_list = [f[-4:] for f in file_list]
        # try:
        #     uploader = '[{}]'.format(self.get_uploader())
        # except BilibiliError:
        #     uploader = ''
        uploader = '[{}]'.format(self.get_uploader() or 'NA')
        output = os.path.join(self.work_dir, '{} [av{}]{}'.format(title, self.id, uploader))
        if len(self.part_list) >= 2:
            part_title = safe_basename(self._current_meta['page_data']['part'])
            output += '{}-{}.mp4'.format(self._current_part, part_title)
        else:
            output += '.mp4'
        safe_print(output)
        if '.m4s' in ext_list:
            m4s_list = [f for f in file_list if f[-4:] == '.m4s']
            merge_m4s(m4s_list, output)
        elif '.blv' in ext_list:
            blv_list = [f for f in file_list if f[-4:] == '.blv']
            concat_videos(blv_list, output)
        else:
            print('    NO MEDIA STREAM FOUND')
        shutil.copy2(os.path.join(self.folder, self._current_part, 'danmaku.xml'), output[:-3] + 'xml')

    def extract_bangumi(self):
        title = safe_basename(self._current_meta['title'])
        blv_list = glob(os.path.join(self.folder, self._current_part, self._current_meta['type_tag'], '*.blv'))
        part_title = safe_basename(self._current_meta['ep']['index_title'])
        av_id = self._current_meta['ep']['av_id']
        ep_num = self._current_meta['ep']['index']
        output_dir = os.path.join(self.work_dir, '{} [av{}][{}]'.format(title, av_id, self.id))
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        output = os.path.join(output_dir, '{}. {}.mp4'.format(str(ep_num).zfill(len(str(self.part_sum))), part_title))
        safe_print(output)
        concat_videos(blv_list, output)
        shutil.copy2(os.path.join(self.folder, self._current_part, 'danmaku.xml'), output[:-3] + 'xml')
