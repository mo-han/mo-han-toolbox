#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import shutil
import sys
from glob import glob
from http.cookiejar import MozillaCookieJar

import requests
import you_get.util.strings
from lxml import html

from .cli import SimpleDrawer
from .misc import safe_print, safe_basename
from .os_nt import win32_ctrl_c_signal
from .struct import modify_and_import
from .video import concat_videos, merge_m4s
from .web import cookie_string_from_dict, cookies_dict_from_file

BILIBILI_VIDEO_URL_PREFIX = 'https://www.bilibili.com/video/'


class BilibiliError(RuntimeError):
    pass


def _tmp(avid, cid):
    param = {'avid': avid, 'cid': cid, 'type': '', 'otype': 'json', 'fnver': 0, 'fnval': 16}
    api_url = 'https://api.bilibili.com/x/player/playurl'
    r = requests.get(api_url, param)
    return r.json()


def modify_you_get_bilibili(x: str):
    x = x.replace('''
    stream_types = [
        {'id': 'flv_p60', 'quality': 116, 'audio_quality': 30280,
         'container': 'FLV', 'video_resolution': '1080p', 'desc': '高清 1080P60'},
''', '''
    stream_types = [
        {'id': 'hdflv2_4k', 'quality': 120, 'audio_quality': 30280,
         'container': 'FLV', 'video_resolution': '2160p', 'desc': '超清 4K'},
        {'id': 'flv_p60', 'quality': 116, 'audio_quality': 30280,
         'container': 'FLV', 'video_resolution': '1080p', 'desc': '高清 1080P60'},
''')
    x = x.replace('''
        elif height <= 1080 and qn <= 80:
            return 80
        else:
            return 112
''', '''
        elif height <= 1080 and qn <= 80:
            return 80
        elif height <= 1080 and qn <= 112:
            return 112
        else:
            return 120
''')
    x = x.replace('''
                log.w('This is a multipart video. (use --playlist to download all parts.)')
''', r'''
                sys.stderr.write('# multi-part video: use -p to download other part(s)\n')
''')
    x = x.replace('''
            # set video title
            self.title = initial_state['videoData']['title']
            # refine title for a specific part, if it is a multi-part video
            p = int(match1(self.url, r'[\?&]p=(\d+)') or match1(self.url, r'/index_(\d+)') or
                    '1')  # use URL to decide p-number, not initial_state['p']
            if pn > 1:
                part = initial_state['videoData']['pages'][p - 1]['part']
                self.title = '%s (P%s. %s)' % (self.title, p, part)
''', '''
            # set video title
            self.title = initial_state['videoData']['title']
            self.title += ' ' + self.get_vid_label() + self.get_author_label()
            # refine title for a specific part, if it is a multi-part video
            p = int(match1(self.url, r'[\?&]p=(\d+)') or match1(self.url, r'/index_(\d+)') or
                    '1')  # use URL to decide p-number, not initial_state['p']
            if pn > 1:
                part = initial_state['videoData']['pages'][p - 1]['part']
                self.title = '%s P%s. %s' % (self.title, p, part)
''')
    x = x.replace('''
                # automatic format for durl: qn=0
                # for dash, qn does not matter
                if current_quality is None or qn < current_quality:
''', '''
                # automatic format for durl: qn=0
                # for dash, qn does not matter
                # if current_quality is None or qn < current_quality:
                if True:
''')
    x = x.replace('''
    def prepare_by_cid(self,avid,cid,title,html_content,playinfo,playinfo_,url):
''', '''
        self.del_unwanted_dash_streams()

    def prepare_by_cid(self, avid, cid, title, html_content, playinfo, playinfo_, url):
''')
    return x


def modify_you_get_fs(x: str):
    x = x.replace("ord('['): '(',", "#ord('['): '(',")
    x = x.replace("ord(']'): ')',", "#ord(']'): ')',")
    x = x.replace('''
    text = text[:80] # Trim to 82 Unicode characters long
''', '''
    text = text[:200] # Trim to 82 Unicode characters long
''')
    return x


you_get.util.fs = modify_and_import('you_get.util.fs', modify_you_get_fs)
you_get.util.strings.legitimize = you_get.util.fs.legitimize
# you_get.extractor.get_filename = you_get.common.get_filename = you_get.util.strings.get_filename
you_get.extractors.bilibili = modify_and_import('you_get.extractors.bilibili', modify_you_get_bilibili)


def get_vid(x: str or int) -> str or None:
    if isinstance(x, int):
        vid = 'av{}'.format(x)
    elif isinstance(x, str):
        for m in (re.search(r'(av\d+)', x), re.search(r'(BV[\da-zA-Z]{10})', x, flags=re.I)):
            if m:
                vid = m.group(1)
                if vid.startswith('bv'):
                    vid = 'BV' + vid[2:]
                break
        else:
            vid = None
    else:
        raise TypeError("'{}' is not str or int".format(x))
    return vid


def download_bilibili_video(url: str or int,
                            cookies: str or dict = None, output: str = None, parts: list = None,
                            qn_max: int = None, qn_single: int = None, moderate_audio: bool = True, fmt=None,
                            info: bool = False, playlist: bool = None,
                            **kwargs):
    win32_ctrl_c_signal()
    dr = SimpleDrawer(sys.stderr.write, '\n')

    if not output:
        output = '.'
    if not qn_max:
        qn_max = 116
    url = BILIBILI_VIDEO_URL_PREFIX + get_vid(url)

    dr.print(url)
    dr.hl()
    bd = YouGetBilibiliX(cookies=cookies, qn_max=qn_max, qn_single=qn_single)

    if info:
        dl_kwargs = {'info_only': True}
    else:
        dl_kwargs = {'output_dir': output, 'merge': True, 'caption': True}
    if fmt:
        dl_kwargs['format'] = fmt
    if moderate_audio:
        bd.set_audio_qn(30232)

    if playlist:
        bd.download_playlist_by_url(url, **dl_kwargs)
    else:
        if parts:
            base_url = url
            for p in parts:
                url = base_url + '?p={}'.format(p)
                dr.print(url)
                dr.hl()
                bd.download_by_url(url, **dl_kwargs)
        else:
            bd.download_by_url(url, **dl_kwargs)


class YouGetBilibiliX(you_get.extractors.bilibili.Bilibili):
    def __init__(self, *args, cookies: str or dict = None, qn_max=116, qn_single=None):
        super(YouGetBilibiliX, self).__init__(*args)
        self.cookie = None
        if cookies:
            self.set_cookie(cookies)
        self.qn_max = qn_max
        self.qn_single = qn_single
        self.html = None, None

    def set_audio_qn(self, qn):
        for d in self.stream_types:
            d['audio_quality'] = qn

    def update_html_doc(self):
        url, doc = self.html
        if url != self.url:
            url = self.url
            headers = self.bilibili_headers()
            r = requests.get(url, headers=headers)
            doc = html.document_fromstring(r.text)
            self.html = url, doc

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
        headers = super(YouGetBilibiliX, self).bilibili_headers(referer=referer, cookie=cookie)
        return headers

    def get_vid(self):
        url = self.url
        for m in [re.search(r'/(av\d+)', url), re.search(r'/(bv\w{10})', url, flags=re.I)]:
            if m:
                vid = m.group(1)
                if vid.startswith('bv'):
                    vid = 'BV' + vid[2:]
                break
        else:
            vid = None
        return vid

    def get_vid_label(self, fmt='[{}]'):
        the_vid = self.get_vid()
        label = fmt.format(the_vid)
        if the_vid.startswith('BV'):
            self.update_html_doc()
            _, h = self.html
            canonical = h.xpath('//link[@rel="canonical"]')[0].attrib['href']
            avid = re.search(r'/(av\d+)/', canonical).group(1)
            label += fmt.format(avid)
        return label

    def get_author(self):
        self.update_html_doc()
        _, h = self.html
        return h.xpath('//meta[@name="author"]')[0].attrib['content']

    def get_author_label(self, fmt='[{}]'):
        return fmt.format(self.get_author())

    def del_unwanted_dash_streams(self):
        format_to_qn_id = {t['id']: t['quality'] for t in self.stream_types}
        for f in list(self.dash_streams):
            q = format_to_qn_id[f.split('-', maxsplit=1)[-1]]
            if q > self.qn_max or self.qn_single and self.qn_single == q:
                del self.dash_streams[f]


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
