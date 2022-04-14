#!/usr/bin/env python3
import json
import re
import urllib.parse

from ezpykit.allinone import *
from ezpykitext.webclient import *

rm_suffix = ezstr.removesuffix
rm_prefix = ezstr.removeprefix

__logger__ = logging.get_logger(__name__)


class BBDownCommandLineList(subprocess.CommandLineList):
    which = 'BBDown'
    enable_short_option_for_word = True

    def set_cookies(self, source):
        cj = cookie.EzCookieJar()
        cj.smart_load(source, ignore_expires=True)
        s = cj.get_header_string('SESSDATA', header='')
        return self.add(c=s)

    def enable_debug(self):
        return self.add('--debug')

    def add_uri(self, uri):
        if isinstance(uri, int) or ezstr.is_int(uri):
            uri = f'av{uri}'
        return self.add(uri)


class BBDownInfo(ezdict):
    ended = False
    sections: ezlist[str]
    KEY_RUNTIME = 'runtime'
    HEAD_APP_DIR = 'AppDirectory: '
    HEAD_RUNTIME_PARAMS = '运行参数：'
    HEAD_WEB_REQUEST = '获取网页内容：'
    HEAD_WEB_RESPONSE = 'Response: '

    @property
    def owner(self):
        return self[['owner', 'name']]

    @property
    def staff(self):
        return [i['name'] for i in self.get('staff', ())]

    @property
    def p_num(self):
        return len(self['P'])

    def end(self):
        self.ended = True

    def parse(self, sections: ezlist):
        self.ended = False
        self.sections = sections
        sections.current_index = -1
        callee = self.start
        while not self.ended:
            if isinstance(callee, tuple):
                callee_ = callee[0]
                args = callee[1:]
                __logger__.debug((callee_.__name__, args))
                callee = callee_(*args)
            else:
                __logger__.debug(callee.__name__)
                callee = callee()
        return self.postprocess()

    def postprocess(self):
        pages = self['pages']
        for page_d in pages:
            p = page_d['page']
            d = ezdict.pick(page_d, 'part', 'cid')
            ezdict.rekey(d, 'part', 'title')
            self[['P', p]].update(d)
        self.remove(self.KEY_RUNTIME)
        # self.reserve('P', 'aid', 'bvid', 'tname', 'title', 'desc', 'owner', 'staff')
        return self

    def start(self):
        return self.s_section

    @staticmethod
    def _strip(s: str):
        return s.strip('：: ')

    def s_section(self):
        s = self.sections.next
        if s.startswith(self.HEAD_APP_DIR):
            self[[self.KEY_RUNTIME, self._strip(self.HEAD_APP_DIR)]] = rm_prefix(s, self.HEAD_APP_DIR)
            return self.s_section
        if s.startswith(self.HEAD_RUNTIME_PARAMS):
            self[self.KEY_RUNTIME].update(json.loads(rm_prefix(s, self.HEAD_RUNTIME_PARAMS)))
            return self.s_section
        if s.startswith(self.HEAD_WEB_REQUEST):
            url = re.MatchWrapper(re.search('Url: (.+), Headers: ', s)).group(1).strip()
            return self.s_web_response, url
        p = re.MatchWrapper(re.match(r'开始解析P(\d+)...', s)).group(1)
        if p:
            return self.s_p, int(p)
        if s == '任务完成':
            return self.end
        return self.s_section

    def s_p(self, p):
        s = self.sections.next
        if re.match(r'共计\d+条视频流', s):
            k = ['P', p, 'video']
            streams = self.setdefault(k, [])
            for l in s.splitlines():
                m = re.search(r'\d+\. \[(.+)] \[(.+)] \[(.+)] \[(.+)] \[(.+)] \[(.+)]', l)
                if not m:
                    continue
                name, hxw, codec, fps, bitrate, size = m.groups()
                height, width = hxw.split('x')
                d = dict(name=name, codec=codec, height=height, width=width, fps=fps, bitrate=bitrate, size=size)
                streams.append(d)
            return self.s_p, p
        if re.match(r'共计\d+条音频流', s):
            k = ['P', p, 'audio']
            streams = self.setdefault(k, [])
            for l in s.splitlines():
                m = re.search(r'\d+\. \[(.+)] \[(.+)] \[(.+)]', l)
                if not m:
                    continue
                codec, bitrate, size = m.groups()
                d = dict(codec=codec, bitrate=bitrate, size=size)
                streams.append(d)
            return self.s_section
        return self.s_p, p

    def s_web_response(self, url):
        s = self.sections.next
        if s.startswith(self.HEAD_WEB_RESPONSE):
            u = urllib.parse.urlparse(url)
            d = json.loads(rm_prefix(s, self.HEAD_WEB_RESPONSE))['data']
            if u.path in ('/x/web-interface/archive/stat', '/x/web-interface/view'):
                self.update(d)
            else:
                self[u.path] = d
            return self.s_section
        return self.s_web_response, url


class BBDownWrapper:
    def __init__(self, cookie_source=None, which=None):
        self.cmd_temp = BBDownCommandLineList()
        if which:
            self.cmd_temp.set_which(which)
        if cookie_source:
            self.cmd_temp.set_cookies(cookie_source)

    def get_info(self, uri):
        cmd = self.cmd_temp.copy().enable_debug().add(info=True).add_uri(uri)
        p = cmd.popen(stdout=subprocess.PIPE, universal_newlines=True)
        output = p.stdout.read()
        p.wait()
        if p.returncode:
            raise subprocess.CalledProcessError(p.returncode, p.args, f'ERROR: {output.splitlines()[-1]}')
        return BBDownInfo().parse(ezlist(map(str.strip, re.split(r'\[[\d -:.]+] - ', output))))
