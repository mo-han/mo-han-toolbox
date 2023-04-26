#!/usr/bin/env python3
import re
import urllib.parse
from contextlib import suppress

from oldezpykit.allinone import *
from oldezpykitext.webclient import *
from websites import bilibili

rm_suffix = ezstr.removesuffix
rm_prefix = ezstr.removeprefix

__logger__ = logging.get_logger(__name__)


class BBDownVideoStreamQualityLevel(tuple):
    RESOLUTION_ORDER = ezlist.to_dict(['360', '480', '720', '1080', '4K', '8K'])
    SVIP_KEYWORD = ['高帧率', '高码率', 'svip']

    def __new__(cls, stream_dict_or_name):
        bitrate_level = 0
        if isinstance(stream_dict_or_name, dict):
            name = stream_dict_or_name['name']
        else:
            name = stream_dict_or_name
        for k, v in cls.RESOLUTION_ORDER.items():
            if v.lower() in name.lower():
                resolution_level = k
                break
        else:
            raise ValueError('invalid video quality name', name)
        for k in cls.SVIP_KEYWORD:
            if k in name:
                bitrate_level += 1
        return super().__new__(cls, (resolution_level, bitrate_level))


class BBDownCommandLineList(subprocess.CommandLineList):
    exec = 'BBDown'
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
    aux_api: bilibili.webapi.BilibiliWebAPI
    vid: dict
    reserved_keys = {'p', 'aid', 'bvid', 'tname', 'title', 'desc', 'owner', 'staff', 'avid'}
    stopped = False
    sections: ezlist[str]
    KEY_RUNTIME = 'runtime'
    HEAD_APP_DIR = 'AppDirectory: '
    HEAD_RUNTIME_PARAMS = '运行参数：'
    HEAD_WEB_REQUEST = '获取网页内容：'
    HEAD_WEB_RESPONSE = 'Response: '

    def __getattr__(self, item):
        if item in self:
            return self[item]
        else:
            raise AttributeError(item)

    @property
    def owner(self):
        return self[['owner', 'name']]

    @property
    def staff(self):
        return [i['name'] for i in self.get('staff', ())]

    @property
    def tags(self):
        return self.aux_api.get_tags(self.vid)

    @property
    def replies_text(self):
        return self.aux_api.get_replies(self.vid, text=True)

    @property
    def info_file_text(self):
        return '\n---\n'.join((self['desc'], '  '.join(self.tags), self.replies_text))

    @property
    def creator_text(self):
        if self.staff:
            n = len(self.staff)
            if n > 1:
                cl = [self.staff[0], f'等{n}位']
            else:
                cl = [self.staff[0]]
        else:
            cl = [self.owner]
        return ' '.join(cl)

    @property
    def vid_text(self):
        return ' '.join(self.pick_to_list('bvid', 'avid'))

    @property
    def preferred_filename(self):
        return ezstr.to_sanitized_path(f"{self['title']} [bilibili {self.vid_text}][{self.creator_text}]")

    def preferred_filename_with_p(self, p):
        fp = ezstr.to_sanitized_path(f"{self.preferred_filename} P{p}. {self[['p', p, 'title']]}")
        return ezstr.ellipt_end(fp, 200, encoding='utf8')

    @property
    def p_count(self):
        return len(self['p'])

    @property
    def is_multi_p(self):
        return self.p_count > 1

    def find_preferred_video_stream(self, p, max_video_quality: str):
        p = int(p)
        preferred_codecs_order = ['HEVC', 'AVC']
        max_video_quality_level = BBDownVideoStreamQualityLevel(max_video_quality)
        streams_l = filter(lambda x: BBDownVideoStreamQualityLevel(x) <= max_video_quality_level,
                           self[['p', p, 'video']].values())
        streams_ll = sorted_with_equal_groups(streams_l, reverse=True, sort_key=BBDownVideoStreamQualityLevel,
                                              equal_key=lambda x, y: x['name'] == y['name'])
        best_streams_l = streams_ll[0]
        for preferred_codec in preferred_codecs_order:
            for s in best_streams_l:
                if s['codec'] == preferred_codec:
                    return s
        return best_streams_l[0]

    def stop(self):
        self.stopped = True

    def parse(self, sections: ezlist, aux_api: bilibili.webapi.BilibiliWebAPI):
        self.aux_api = aux_api
        self.stopped = False
        self.sections = sections
        sections.current_index = -1
        callee = self.start
        while not self.stopped:
            callee, args, kwargs = call.unpack_callee_args_kwargs(callee)
            __logger__.debug((callee.__name__, args, kwargs))
            callee = callee(*args, **kwargs)
        return self.postprocess()

    def postprocess(self, debug=False):
        self.vid = self.aux_api.parse_vid_dict(self.pick('aid', 'bvid'))
        self['avid'] = f'av{self["aid"]}'
        pages = self['pages']
        for page_d in pages:
            p = page_d['page']
            d = ezdict.pick(page_d, 'part', 'cid')
            with suppress(KeyError):
                d['title'] = d.pop('part')
            self[['p', p]].update(d)
        if not debug:
            for key in {self.KEY_RUNTIME, *(self.keys() - self.reserved_keys)}:
                with suppress(KeyError):
                    del self[key]
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
            return self.stop
        return self.s_section

    @staticmethod
    def _split_bitrate(s: str):
        value, unit = s.split()
        return int(value), unit

    def s_p(self, p):
        s = self.sections.next
        if re.match(r'共计\d+条视频流', s):
            k = ['p', p, 'video']
            for l in s.splitlines():
                m = re.search(r'(\d+)\. \[(.+)] \[(.+)] \[(.+)] \[(.+)] \[(.+)] \[(.+)]', l)
                if not m:
                    continue
                index, name, hxw, codec, fps, bitrate, size = m.groups()
                height, width = hxw.split('x')
                index = int(index)
                bitrate = self._split_bitrate(bitrate)
                _locals = locals()
                d = {k: _locals[k] for k in ('index', 'name', 'codec', 'height', 'width', 'fps', 'bitrate', 'size')}
                self[[*k, index]] = d
            return self.s_p, p
        if re.match(r'共计\d+条音频流', s):
            k = ['p', p, 'audio']
            for l in s.splitlines():
                m = re.search(r'(\d+)\. \[(.+)] \[(.+)] \[(.+)]', l)
                if not m:
                    continue
                index, codec, bitrate, size = m.groups()
                index = int(index)
                bitrate = self._split_bitrate(bitrate)
                _locals = locals()
                d = {k: _locals[k] for k in ('index', 'codec', 'bitrate', 'size')}
                self[[*k, index]] = d
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
        self.logger = logging.get_logger(__name__, self.__class__.__name__)
        self.aux_api = bilibili.webapi.BilibiliWebAPI()
        self.cmd_temp = BBDownCommandLineList()
        if which:
            self.cmd_temp.set_which(which)
        if cookie_source:
            self.aux_api.set_cookies(cookie_source)
            self.cmd_temp.set_cookies(cookie_source)

    @property
    def cmd(self):
        return self.cmd_temp.copy()

    def get_video_info(self, uri):
        try:
            uri = f'av{int(uri)}'
        except ValueError:
            pass
        uri = self.aux_api.clarify_uri(uri)
        cmd = self.cmd.enable_debug().add(info=True).add_uri(uri)
        p = cmd.popen(stdout=subprocess.PIPE, universal_newlines=True)
        output = p.stdout.read()
        p.wait()
        if p.returncode:
            raise subprocess.CalledProcessError(p.returncode, p.args, f'ERROR: {output.splitlines()[-1]}')
        return BBDownInfo().parse(ezlist(map(str.strip, re.split(r'\[[\d -:.]+] - ', output))), self.aux_api)

    def _dl_single(self, uri, p, video_stream_index, audio_stream_index):
        cmd = self.cmd.add(uri, ia=True, p=p, dd=True, use_aria2c=True)
        return cmd.run(input=f'{video_stream_index}\n{audio_stream_index}\n', universal_newlines=True)

    def dl_single(self, uri, p, video_stream_index, audio_stream_index, filename):
        expected_files_ext = {'.mp4': '.mp4', '.ass': '.danmaku-ass', '.xml': '.xml'}
        with tempfile.TemporaryDirectory(prefix=self.__class__.__name__ + '-') as dp:
            with os.ctx_pushd(dp):
                while True:
                    self._dl_single(uri, p, video_stream_index, audio_stream_index)
                    expected_filenames = list(filter(lambda x: os.split_ext(x)[1] in expected_files_ext, os.listdir()))
                    if len(expected_filenames) == 3:
                        break
            expected_filenames = [os.join_path(dp, i) for i in expected_filenames]
            for fp in expected_filenames:
                new_fp = filename + expected_files_ext[os.split_ext(fp)[1]]
                shutil.move_to(fp, new_fp, overwrite=True, follow_symlinks=True)
                self.logger.info(f'{new_fp} <- {fp}')

    def dl_info(self, video_info: BBDownInfo):
        fp = video_info.preferred_filename + '.info'
        io.IOKit.write_exit(open(fp, 'w', encoding='utf-8-sig'), video_info.info_file_text)
        self.logger.info(fp)

    def dl(self, video_info: BBDownInfo, p_range=None,
           max_video_quality='1080svip'):
        if not isinstance(video_info, BBDownInfo):
            video_info = BBDownInfo(video_info)
        if isinstance(p_range, str):
            p_range = StrKit.to_range(p_range, default_end=video_info.p_count)
        p_range = p_range or range(1, video_info.p_count + 1)
        uri = video_info.pick_to_list('bvid', 'avid')[0]
        for p in p_range:
            asi = 0
            vsi = video_info.find_preferred_video_stream(p, max_video_quality)['index']
            fn = video_info.preferred_filename if video_info.p_count == 1 else video_info.preferred_filename_with_p(p)
            self.dl_single(uri, p, vsi, asi, fn)
        self.dl_info(video_info)
