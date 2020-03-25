#!/usr/bin/env python3
# encoding=utf8
import sys
from glob import glob
from os import rename
from os.path import split, splitext, join
from urllib.parse import urlparse

from lxml import html
from requests import get


class IwaraVideo:
    def __init__(self, url: str):
        self.urlparse = urlparse(url)
        if 'iwara' not in self.urlparse.hostname:
            raise ValueError(url)
        elif 'video' not in self.urlparse.path:
            raise ValueError(url)
        self.url = url
        self.html = None
        self.meta = {
            'id': self.urlparse.path.split('/')[-1],
        }

    def get_page(self):
        if not self.html:
            r = get(self.url)
            self.html = html.document_fromstring(r.text)
        return self.html

    def get_uploader(self):
        key_str = 'uploader'
        if key_str in self.meta:
            return self.meta[key_str]
        else:
            video_page = self.get_page()
            uploader = video_page.xpath('//div[@class="node-info"]//div[@class="submitted"]//a[@class="username"]')[0].text
            self.meta[key_str] = uploader
            return uploader

    def find_files_by_id(self, search_in=''):
        id_tag = '[{}]'.format(self.meta['id'])
        self.meta['id_tag'] = id_tag
        mp4_l = glob(search_in + '*.mp4')
        r_l = []
        for i in mp4_l:
            if id_tag in i:
                r_l.append(i)
        return r_l

    def rename_files_from_ytdl_na_to_uploader(self, search_in=''):
        na_tag = '[NA]'
        path_l = self.find_files_by_id(search_in=search_in)
        id_tag = self.meta['id_tag']
        uploader = self.get_uploader()
        up_tag = '[{}]'.format(uploader)
        for p in path_l:
            dirname, basename = split(p)
            filename, extension = splitext(basename)
            if na_tag in filename:
                left, right = filename.split(id_tag, maxsplit=1)
                right = right.replace(na_tag, up_tag, 1)
                new_basename = left + id_tag + right + extension
                new_path = join(dirname, new_basename)
                rename(p, new_path)


if __name__ == '__main__':
    u = sys.argv[1]
    video = IwaraVideo(u)
    video.rename_files_from_ytdl_na_to_uploader()
