#!/usr/bin/env python3
import json
import os
import re
import shutil
import time
from glob import glob
from http.cookiejar import MozillaCookieJar
from typing import Tuple

import requests
# 下面导入的是通过pip安装的you-get
# 如果仅仅`import you_get`，模块名空间`sys.modules`中不会包含`you_get.util.strings`
# 但`you_get.util.strings`这个路径在后续用得到，you-get的另外几个模块需要从这个路径导入函数
import you_get.util.strings
from lxml import html

import oldezpykitext.webclient.header
from mylib import web_client
from mylib.__deprecated__ import concat_videos, merge_m4s
from mylib._misc import safe_print, safe_basename
from mylib.easy import python_module_from_source_code, str_remove_suffix
from mylib.ext import fstk
from mylib.ext import http_headers
from mylib.ext.ostk import ensure_sigint_signal
from mylib.ext.text import regex_find, ellipt_end
from mylib.ext.tricks import str2range, seq_call_return
from mylib.ext.tui import LinePrinter
from websites.bilibili import webapi

BILIBILI_VIDEO_URL_PREFIX = 'https://www.bilibili.com/video/'
BILIBILI_EPISODE_URL_PREFIX = 'https://www.bilibili.com/bangumi/play/'
BILIBILI_SHORT_URL_PREFIX = 'https://b23.tv/'
QUALITY_DESC_PRIORITY = ['超清 4K', '高清 1080P60', '高清 1080P+', '高清 720P60', '高清 1080P', '高清 720P',
                         '清晰 480P', '流畅 360P']

bilibili_webapi = webapi.BilibiliWebAPI(cache_request=True)


def quality_desc_priority_index(quality_desc: str):
    return QUALITY_DESC_PRIORITY.index(quality_desc)


class BilibiliError(RuntimeError):
    pass


# def _tmp(avid, cid):
#     param = {'avid': avid, 'cid': cid, 'type': '', 'otype': 'json', 'fnver': 0, 'fnval': 16}
#     api_url = 'https://api.bilibili.com/x/player/playurl'
#     r = requests.get(api_url, param)
#     return r.json()


# 这个函数用于修改you-get的B站下载模块`you_get.extractors.bilibili`的源码
def code_modify_you_get_bilibili(x: str):
    # `x`是输入的源代码字符串，就也是原版模块的源代码
    # 对其进行替换，在要替换的代码的上下文中，截取特征明显的一段，然后直接replace

    # 下面也是跟4K相关的判断代码
    # B站视频流用不同数字ID标定不同的格式码率，120是4K，112则是大会员的1080P+（即较高码率的1080P30）
    # （116是大会员1080P60，从实际效果来看，无需对116作判断）
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
    # 下面这段修改了原本代码中的一行提示打印文本，以便和自己写的命令行工具所设计的选项保持一致
    x = x.replace('''
                log.w('This is a multipart video. (use --playlist to download all parts.)')
''', r'''
                sys.stderr.write('# multi-part video: use -p to download other part(s)\n')
''')
    # 下面这段修改了下载文件名的格式，原版是视频标题+选集子标题
    # 在视频标题+选集子标题的基础上，插入了一些有用的元信息：[av号][BV号][上传者用户名]
    # bookmark: title manipulation
    x = x.replace('''
                if pn > 1:
                    part = initial_state['videoData']['pages'][p - 1]['part']
''', '''
                if pn > 1:
                    part = initial_state['videoData']['pages'][p - 1]['part']
                    self.whole_main_title = self._make_the_title_in_my_flavor(ellipt=False)
                    self.file_title = self._make_the_title_in_my_flavor()
                    self.part_title = self._make_the_title_in_my_flavor((p, part))
''')
    # 下面这段是个重点，修改的是原版中`you_get.extractors.bilibili.Bilibili.prepare_by_url`这个方法函数
    # 原版you-get对相当多的B站视频无法获取大会员的1080P+、1080P60等格式
    # 原版这里的逻辑有问题，按下面这样修改后，用到现在没发现异常
    # 根本原因没有彻底搞明白，但肯定与原版代码中`current_quality`和`best_quality`的判定有关
    x = x.replace('''
            # get alternative formats from API
            for qn in [112, 80, 64, 32, 16]:
                # automatic format for durl: qn=0
                # for dash, qn does not matter
                if current_quality is None or qn < current_quality:
''', '''
            # get alternative formats from API
            for qn in [116, 112, 80, 64, 32, 16]:
                # automatic format for durl: qn=0
                # for dash, qn does not matter
                # if current_quality is None or qn < current_quality:
                if True:
''')
    # 下面这段，修改的是原版`you_get.extractors.bilibili.Bilibili.prepare_by_url`的结尾部分
    # 新加一个流程，从已经获取的所有视频流格式中，删除一部分不需要的格式
    # you-get默认下载最佳画质，虽然可以选择画质，但用的格式名称比较长，不如数字ID本身来得方便
    # 所以加了一个`del_unwanted_dash_streams()`，用数字来指定最高画质和需要下载的画质
    # （其实加这个方法，还是因为Bug修得不彻底，权宜之计罢了）
    # 顺便一提，这个`del_unwanted_dash_streams`方法不是原版you-get代码里自带的
    # 而是在新的`YouGetBilibiliX`类里自定义的方法
    # 而`YouGetBilibiliX`则是继承的修改版`bilibili.Bilibili`
    # 替换原版代码 -> 调用一个原版没有的方法 -> 修改版 -> 继承修改版的新类 -> 在新类中补上这个缺失的方法
    # 回溯套娃，左右横跳！
    x = x.replace('''
    def prepare_by_cid(self,avid,cid,title,html_content,playinfo,playinfo_,url):
''', '''
        self.del_unwanted_dash_streams()

    def prepare_by_cid(self, avid, cid, title, html_content, playinfo, playinfo_, url):
''')
    return x


# 下面这个函数用于修改you-get的文件系统模块`you_get.util.fs`的源码
def code_modify_you_get_fs(x: str):
    # 原版为了兼容VFAT文件系统，会把文件名里面的方括号替换成圆括号
    # 修改版不需要这个特性，所以将这两行代码加#注释掉了
    x = x.replace("ord('['): '(',", "#ord('['): '(',")
    x = x.replace("ord(']'): ')',", "#ord(']'): ')',")
    # 下面把最大文件名字符串长度从80延长到200，原版的80有点小，200会不会太大尚不清楚
    x = x.replace('''
    text = text[:80] # Trim to 82 Unicode characters long
''', '''
    text = text[:200]
''')
    return x


def code_modify_you_get_extractor(x: str):
    x = x.replace("key=lambda i: -self.dash_streams[i]['size']",
                  "key=lambda i: quality_desc_priority_index(self.dash_streams[i]['quality'])")
    return x


def new_legitimize(text: str, os=...):
    m = re.match(r'(.+)( \[bilibili .+)', text)
    if m:
        title, suffix = m.groups()
        title = ellipt_end(fstk.sanitize(title, fstk.POTENTIAL_INVALID_CHARS_MAP), 230, encoding='utf8')
        text = title + suffix
    return ellipt_end(fstk.sanitize(text, fstk.POTENTIAL_INVALID_CHARS_MAP), 230, encoding='utf8').lstrip('.')


you_get.extractor = python_module_from_source_code('you_get.extractor', code_modify_you_get_extractor)
you_get.extractor.quality_desc_priority_index = quality_desc_priority_index
# 上面已经导入了原版的`you_get.util.strings`，这条模块路径很重要，另有几个模块依赖它
# 在此基础上，下面一行代码将原版的`you_get.util.fs`模块替换成修改版（弃用，不再修改原版模块，换用新的`new_legitimize`函数）
# you_get.util.fs = modify_module('you_get.util.fs', code_modify_you_get_fs)
# 接着把原版中的`you_get.util.strings.legitimize`函数替换成修改版`you_get.util.fs`中的对应函数
you_get.util.strings.legitimize = you_get.util.fs.legitimize = new_legitimize
# （上面的`code_modify_you_get_fs`修改的正是`legitimize`）
# 在原版的you-get中，`.util.string`从`.util.fs`中导入了`legitimize`这个函数
# `.util.string`又利用这个导入的`legitimize`和其他几个函数，构建了一个`get_filename`函数
# 而`you_get.extractor`和`you_get.common`又都用到了`get_filename`，当然是各自分别从`you_get.util.strings`导入的
# 因此，所以，故而，然则，
# 只要将原版`you_get.util.strings.legitimize`替换成修改版的`you_get.util.fs.legitimize`即可
# 那些从`you_get.util.strings`导入`legitimize`函数的模块会自动导入已被替换的修改版
# 综上所述，下面这行可以注释掉了（已经注释掉了）
# you_get.extractor.get_filename = you_get.common.get_filename = you_get.util.strings.get_filename
# 下面则是将B站下载模块替换成修改版，所用的源码替换函数是`code_modify_you_get_bilibili`
you_get.extractors.bilibili = python_module_from_source_code('you_get.extractors.bilibili',
                                                             code_modify_you_get_bilibili)
you_get_filename = you_get.util.strings.get_filename


# 搜寻av、BV、AV、bv开头的字符串或者整形数，将之变成B站视频的av号或者BV号
def find_bilibili_vid(x: str or int) -> str or None:
    if isinstance(x, int):
        vid = 'av{}'.format(x)
    elif isinstance(x, str):
        for p in (r'(BV[\da-zA-Z]{10})', r'(av\d+)',):
            m = re.search(p, x, flags=re.I)
            if m:
                vid = m.group(1)
                if vid.startswith('bv'):
                    vid = 'BV' + vid[2:]
                elif vid.startswith('AV'):
                    vid = 'av' + vid[2:]
                break
        else:
            vid = None
    else:
        raise TypeError("'{}' is not str or int".format(x))
    return vid


def vid_to_bvid_via_web_api(vid: str or int, cookies: dict = None) -> str or None:
    bilibili_webapi.set_cookies(cookies)
    return bilibili_webapi.parse_vid_dict(vid)['bvid']


def bilibili_url_from_vid(vid: str) -> str:
    if vid[:2] in ('BV', 'av'):
        return BILIBILI_VIDEO_URL_PREFIX + vid
    elif vid[:2] in ('ep', 'ss'):
        return BILIBILI_EPISODE_URL_PREFIX + vid
    else:
        return BILIBILI_SHORT_URL_PREFIX + vid


# `YouGetBilibiliX`继承了`you_get.extractors.bilibili.Bilibili`，添加了一些新的功能
# 其中包含了`del_unwanted_dash_streams`这个新方法
# 但是对`del_unwanted_dash_streams`的调用却是在被继承的`Bilibili`（的修改版）中进行的
# noinspection PyUnresolvedReferences
class YouGetBilibiliX(you_get.extractors.bilibili.Bilibili):
    # stream_types =
    url: str

    def __init__(self, *args, cookies: str or dict = None, qn_max=116, qn_want=None):
        super().__init__(*args)
        self.bilibili_webapi = bilibili_webapi
        self.do_not_write_any_file = False
        self.cookie = None
        if cookies:
            self.set_cookie(cookies)
        self.qn_max = qn_max
        self.qn_want = qn_want
        # noinspection PyTypeChecker
        self.cache_url_html: Tuple[str, web_client.HTMLElementTree] = (None, None)

    def _make_the_title_in_my_flavor(self, part_num_title_t=(), ellipt=120):
        if ellipt:
            r = ellipt_end(self.the_title, ellipt, encoding='utf8') + \
                ' ' + self.get_vid_label() + ' ' + self.get_author_label()
        else:
            r = self.the_title + ' ' + self.get_vid_label() + ' ' + self.get_author_label()
        if part_num_title_t:
            part_num, part_title = part_num_title_t
            r += f' P.{part_num} {part_title}'
        return r

    def prepare(self, **kwargs):
        self.video_url = self.url
        self.html_etree = web_client.get_html_element_tree(self.video_url, headers=self.bilibili_headers())
        super().prepare(**kwargs)
        self.origin_title = self.title
        if hasattr(self, 'part_title'):
            self.title = self.part_title
        else:
            self.whole_main_title = self._make_the_title_in_my_flavor(ellipt=False)
            self.file_title = self.title = self._make_the_title_in_my_flavor()

    # B站视频的音频流分不同档次，选择中档128kbps就足够了，也可以选择最高音质
    # 低档30216码率偏低，30232约128kbps，30280可能是320kbps也可能是128kbps，貌似跟4K有关，尚不确定
    def set_audio_qn(self, qn):
        for d in self.stream_types:
            d['audio_quality'] = qn

    # 设置cookies，大会员用得着
    # `cookie_str_from_dict`和`cookie_str_from_dict`这两个函数另有定义
    # 前者将cookies字典变成单字符串，后者负责读取cookies文件
    def set_cookie(self, cookies: str or dict):
        if isinstance(cookies, dict):
            cookie_str = http_headers.make_cookie_str(cookies)
        elif isinstance(cookies, str):
            cookie_str = http_headers.make_cookie_str(http_headers.get_cookies_dict_from(cookies))
        else:
            raise TypeError("'{}' is not cookies file path or single-line cookie str or cookies dict".format(cookies))
        self.cookie = cookie_str
        self.bilibili_webapi.cookies = http_headers.parse_cookie_str(cookie_str)

    def bilibili_headers(self, referer=None, cookie=None):
        if not cookie:
            cookie = self.cookie
        headers = super().bilibili_headers(referer=referer, cookie=cookie)
        return headers

    @property
    def the_title(self):
        if not hasattr(self, 'title') or not self.title:
            self.prepare()
        return self.title

    def write_info_file(self, fp: str = None):
        if self.do_not_write_any_file:
            return
        fp = fp or self.whole_main_title + '.info'
        fp = you_get_filename(fp)
        print(fp)
        desc = self.get_desc()
        tags = str(self.get_tags())
        reply = self.get_reply()
        with open(fp, 'w', encoding='utf-8-sig') as f:
            separator = '\n---\n'
            paragraphs = [
                re.sub(r'收起$', '', desc),
                self.whole_main_title + '\n' + re.split(r'\?p=\d+', self.video_url)[0],
                tags, reply
            ]
            f.write(separator.join(paragraphs))

    def get_reply(self):
        try:
            # from websites.bilibili.webapi import BilibiliWebAPI
            # return BilibiliWebAPI().get_replies(self.video_url, text=True)
            return self.bilibili_webapi.get_replies(self.video_url, text=True)
        except Exception as e:
            print(f'! {e}: {e!r}')
            return ''

    def get_desc(self):
        h = self.html_etree
        desc = seq_call_return((
            {'target': lambda: h.xpath('//div[@id="v_desc"]')[0].text_content()},
            # {'target': lambda: h.xpath('//meta[@name="description"]')[0].attrib['content']},
            {'target': lambda: h.cssselect('[class^=video-desc]')[0].text_content()},
            {'target': lambda: h.cssselect('.video-desc')[0].text_content()},
            {'target': lambda: h.cssselect('.media-desc.webkit-ellipsis')[0].text_content()},
            {'target': lambda: '(no desc)'}
        ))
        return desc

    def get_tags(self):
        h = self.html_etree
        return [e.text_content().strip() for e in h.xpath('//*[@class="tag-link"]')]

    # 从URL和HTML获取av号BV号
    def get_vid(self, url=None):
        url = url or self.video_url
        for m in [
            re.search(r'/(bv\w{10})', url, flags=re.I),
            re.search(r'/(av\d+)', url),
            re.search(r'/(ep\d+)', url),
            re.search(r'/(ss\d+)', url)
        ]:
            if m:
                vid = m.group(1)
                if vid.startswith('bv'):
                    vid = 'BV' + vid[2:]
                break
        else:
            vid = ''
        return vid

    def get_real_url(self, url=None):
        vid = self.get_vid(url)
        if vid[:2] in ('ep', 'ss',):
            prefix = BILIBILI_EPISODE_URL_PREFIX
        else:
            prefix = BILIBILI_VIDEO_URL_PREFIX
        return prefix + vid

    def get_vid_label(self):
        # [bilibili <BV_id> <av_id>]
        the_vid = self.get_vid()
        if the_vid.startswith('BV'):
            h = self.html_etree
            # canonical = h.xpath('//link[@rel="canonical"]')[0].attrib['href']
            # av_id = re.search(r'/(av\d+)/', canonical).group(1)  # canonical 也变成BVID了
            # time.sleep(8)  # [Code -799] 请求过于频繁，请稍后再试。但是没用~~~
            # av_id = f'av{self.bilibili_webapi.bvid2aid(the_vid)}'
            id_str = f'{the_vid}'
        elif the_vid.startswith('ep'):
            h = self.html_etree
            og_url = h.xpath('//meta[@property="og:url"]')[0].attrib['content']
            ss_id = re.search(r'/play/(ss\d+)', og_url).group(1)
            id_str = f'{the_vid} {ss_id}'
        else:
            id_str = the_vid
        return f'bilibili {id_str}'

    # 上传者（UP主）用户名
    def get_author(self):
        h = self.html_etree
        return seq_call_return([
            {'target': lambda: h.xpath('//meta[@name="author"]')[0].attrib['content']},
            {'target': lambda: h.cssselect('.staff-multi .info-name')[0].text},
        ])

    def get_author_label(self):
        return f'[{self.get_author()}]'

    # 根据限定的最高画质或者选择的下载画质，从解析得到的视频流中，删除多余的、用不到的
    def del_unwanted_dash_streams(self):
        format_to_qn_id = {t['id']: t['quality'] for t in self.stream_types}
        for f in list(self.dash_streams):
            q = format_to_qn_id[f.split('-', maxsplit=1)[-1]]
            if q > self.qn_max or self.qn_want and self.qn_want != q:
                del self.dash_streams[f]


# 这是一个任务函数，包装了修改版的you-get的B站下载功能，供另外编写的命令行工具调用
def download_bilibili_video(url: str or int,
                            cookies: str or dict = None, output: str = None, parts: list = None,
                            qn_max: int = 116, qn_want: int = None, moderate_audio: bool = True, fmt=None,
                            info: bool = False, playlist: bool = False, caption: bool = True,
                            **kwargs):
    # 确保在Windows操作系统中，SIGINT信号能够被传递到下层扩展中，从而确保Ctrl+C能够立即停止程序
    ensure_sigint_signal()
    lp = LinePrinter()
    if kwargs.get('force') or kwargs.get('overwrite'):
        import you_get.common
        you_get.common.force = True
    b = YouGetBilibiliX(cookies=cookies, qn_max=qn_max, qn_want=qn_want)

    if not output:
        output = '.'
    if '://' not in url:
        url = bilibili_url_from_vid(vid_to_bvid_via_web_api(find_bilibili_vid(url) or url))
    if (url.startswith('https://b23.tv/BV') and len(url) == 22) or (
            url.startswith('https://b23.tv/') and url[15:17] not in ('BV', 'ss', 'ep', 'av')):
        url = bilibili_webapi.clarify_uri(url).split('?', maxsplit=1)[0]
        # r = requests.get(url)
        # if r.ok:
        #     url = r.url.split('?', maxsplit=1)[0]
    b.url = url = b.get_real_url(url)
    lp.print(b.url)

    if info:
        dl_kwargs = {'info_only': True}
    else:
        dl_kwargs = {'output_dir': output, 'merge': True, 'caption': caption}
    if fmt:
        dl_kwargs['format'] = fmt
    if moderate_audio:
        b.set_audio_qn(30232)

    lp.l(shorter=1)
    if playlist:
        b.download_playlist_by_url(url, **dl_kwargs)
    else:
        if parts:
            base_url = url
            parts = str2range(','.join(parts))
            for p in parts:
                url = base_url + '?p={}'.format(p)
                lp.print()
                lp.print(url)
                lp.l(shorter=1)
                b.download_by_url(url, **dl_kwargs)
        else:
            b.download_by_url(url, **dl_kwargs)
    b.write_info_file()


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

    def get_bvid(self):
        url = 'https://api.bilibili.com/x/web-interface/archive/stat?aid={}'.format(self.id)
        param = {}
        if self.cookies:
            param['cookies'] = self.cookies
        r = requests.get(url, **param)
        j = r.json()
        if j['code'] == 0 and j['data']:
            return j['data']['bvid']
        else:
            return None

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
        bvid = self.get_bvid()
        if bvid:
            bv_label = '[{}]'.format(bvid)
        else:
            bv_label = ''
        output = os.path.join(self.work_dir, '{} {}[av{}]{}'.format(title, bv_label, self.id, uploader))
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


def find_url_in_text(text: str) -> list:
    pattern = re.compile(r'(BV[\da-zA-Z]{10}|av\d+|AV\d+|ep\d+|ss\d+)')
    urls = [bilibili_url_from_vid(vid) for vid in regex_find(pattern, text, dedup=True)]
    return urls
