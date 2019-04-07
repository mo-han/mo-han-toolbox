#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import shutil
from glob import glob

from lib_ffmpeg import concat_videos
from lib_misc import safe_print, safe_basename, get_headless_browser


class BilibiliError(RuntimeError):
    pass


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
        if new_name[-5:] == '].ass' and new_name[-8:-5] != '+弹幕':
            new_name = new_name[:-5] + '+弹幕].ass'
        elif new_name[-5:] == '].xml' and new_name[-8:-5] != '+弹幕':
            new_name = new_name[:-5] + '+弹幕].xml'
        elif new_name[-6:] == 'lv.mp4':
            new_name = new_name[:-8] + '.mp4'
        print('{} -> {}'.format(name, new_name))
        new_filepath = path_join(parent, new_name)
        rename(filepath, new_filepath)

    if isfile(path):
        _ren_file(path)
    elif isdir(path):
        for i in [path_join(path, f) for f in os.listdir(path)]: _ren_file(i)
    else:
        print('Not exist: {}'.format(path))


class AppOfflineCacheFolder:
    browser = get_headless_browser()

    def __init__(self, vid_dir_path):
        self.folder = vid_dir_path
        self.work_dir, self.id = os.path.split(os.path.realpath(vid_dir_path))
        self.part_list = os.listdir(vid_dir_path)
        self.part_sum = len(self.part_list)
        self.part = None
        self.entry = None

    def get_uploader(self):
        url = 'https://www.bilibili.com/video/av{}/'.format(self.id)
        self.browser.visit(url)
        meta_author = self.browser.find_by_xpath('//meta[@name="author"]').first.outer_html
        author = meta_author.split('content="')[-1].split('"')[0]
        if author:
            return author
        else:
            raise BilibiliError('No author found.')

    def handle_part(self):
        print('+ {}'.format(self.folder))
        for part in self.part_list:
            self.part = part
            print('  + {}'.format(part), end=': ')
            try:
                self.entry = entry = json.load(open(os.path.join(self.folder, part, 'entry.json'), encoding='utf8'))
            except FileNotFoundError:
                os.remove(os.path.join(self.folder, part))
                continue
            if 'page_data' in entry:
                self.handle_vupload()
            elif 'ep' in entry:
                self.handle_bangumi()

    def handle_vupload(self):
        title = safe_basename(self.entry['title'])
        blv_list = glob(os.path.join(self.folder, self.part, self.entry['type_tag'], '*.blv'))
        try:
            uploader = self.get_uploader()
        except BilibiliError:
            uploader = 'na'
        output = os.path.join(self.work_dir, '{} [av{}][{}]'.format(title, self.id, uploader))
        if len(self.part_list) >= 2:
            part_title = safe_basename(self.entry['page_data']['part'])
            output += '{}-{}.mp4'.format(self.part, part_title)
        else:
            output += '.mp4'
        safe_print(output)
        concat_videos(blv_list, output)
        shutil.copy2(os.path.join(self.folder, self.part, 'danmaku.xml'), output[:-3] + 'xml')

    def handle_bangumi(self):
        title = safe_basename(self.entry['title'])
        blv_list = glob(os.path.join(self.folder, self.part, self.entry['type_tag'], '*.blv'))
        part_title = safe_basename(self.entry['ep']['index_title'])
        av_id = self.entry['ep']['av_id']
        ep_num = self.entry['ep']['index']
        output_dir = os.path.join(self.work_dir, '{} [av{}][{}]'.format(title, av_id, self.id))
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        output = os.path.join(output_dir, '{}. {}.mp4'.format(str(ep_num).zfill(len(str(self.part_sum))), part_title))
        safe_print(output)
        concat_videos(blv_list, output)
        shutil.copy2(os.path.join(self.folder, self.part, 'danmaku.xml'), output[:-3] + 'xml')
