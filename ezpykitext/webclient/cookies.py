#!/usr/bin/env python3
import json

from ezpykit.allinone import io, os, ezlist, ezstr
from ezpykit.stdlib.http.cookiejar import MozillaCookieJar, LoadError

try:
    import requests.cookies as ___
except ImportError:
    if os.system('pip install requests'):
        raise ImportError('failed to install', 'requests')

from requests.cookies import RequestsCookieJar

___ref = RequestsCookieJar

NETSCAPE_HEADER_TEXT = """\
# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do not edit.

"""


class SingleCookieDict(dict):
    class InvalidCookieDict(Exception):
        pass

    def get_netscape_line(self):
        try:
            s_true = 'TRUE'
            s_false = 'FALSE'
            domain = f'#HttpOnly_{self["domain"]}' if self['httpOnly'] else self['domain']
            include_subdomains = s_false if self['hostOnly'] else s_true
            path = self['path']
            secure = s_true if self['secure'] else s_false
            expire = self.get('expirationDate', 0)
            name = self['name']
            value = self['value']
            return '\t'.join([domain, include_subdomains, path, secure, str(expire), name, value])
        except KeyError as e:
            raise self.InvalidCookieDict('missing key', *e.args)


class EzCookieJar(MozillaCookieJar, RequestsCookieJar):
    temp_vfname = f'virtualfile:///EzCookieJar.temp.txt'
    max_vfsize = 1024 * 1024 * 16

    def smart_load(self, source, ignore_discard=False, ignore_expires=False):
        if os.path_isfile(source):
            source = io.IOKit.read_exit(open(source))
        try:
            json.loads(source)
        except json.JSONDecodeError:
            is_json = False
        else:
            is_json = True
        if is_json:
            self.load_json(source, ignore_discard=ignore_discard, ignore_expires=ignore_expires)
        else:
            try:
                self.load_netscape(source, ignore_discard=ignore_discard, ignore_expires=ignore_expires)
            except LoadError:
                try:
                    self.load_string(source)
                except ValueError:
                    raise ValueError('failed to load', source)

    def load_string(self, source, **kwargs):
        if os.path_isfile(source):
            source = io.IOKit.read_exit(open(source))
        cookie_ = 'Cookie:'
        if source.startswith(cookie_):
            ezstr.removeprefix(source, cookie_).strip()
        sep = ';' if ';' in source else ','
        pairs = source.split(sep)
        d = {}
        for p in pairs:
            sep = ':' if ':' in p else '='
            k, v = [s.strip() for s in p.split(sep, maxsplit=1)]
            d[k] = v
        self.update(d)

    def load_json(self, source, ignore_discard=False, ignore_expires=False):
        if os.path_isfile(source):
            source = io.IOKit.read_exit(open(source))
        j = json.loads(source)
        if isinstance(j, dict) and 'cookies' in j:
            j = j['cookies']
        # if isinstance(j, list) and ezlist.first(j) and len(
        #         j[0].keys() & {'name', 'value', 'domain', 'hostOnly', 'path', 'secure', 'httpOnly'}) == 7:
        if isinstance(j, list):
            first = ezlist.get_first(j)
            if not first:
                return
            elif not isinstance(first, dict):
                raise TypeError('cookie dict', type(first))
            SingleCookieDict(first).get_netscape_line()
            netscape_text = self.convert_json_cookies_to_netscape_text(j)
            if len(netscape_text) > self.max_vfsize:
                raise RuntimeError('content too leng', self.max_vfsize, len(netscape_text))
            with io.ctx_open_virtualfileio():
                io.IOKit.write_exit(open(self.temp_vfname, 'w'), netscape_text)
                super().load(self.temp_vfname, ignore_discard=ignore_discard, ignore_expires=ignore_expires)
                return
        raise ValueError('invalid json source')

    def load_netscape(self, source, ignore_discard=False, ignore_expires=False):
        if os.path_isfile(source):
            source = io.IOKit.read_exit(open(source))
        if len(source) > self.max_vfsize:
            raise RuntimeError('content too long', self.max_vfsize, len(source))
        with io.ctx_open_virtualfileio():
            io.IOKit.write_exit(open(self.temp_vfname, 'w'), source)
            super().load(self.temp_vfname, ignore_discard=ignore_discard, ignore_expires=ignore_expires)

    def get_netscape_text(self, ignore_discard=False, ignore_expires=False):
        with io.ctx_open_virtualfileio():
            self.save(self.temp_vfname, ignore_discard=ignore_discard, ignore_expires=ignore_expires)
            return io.IOKit.read_exit(open(self.temp_vfname))

    def get_dict(self, *names, domain=None, path=None):
        d = super(EzCookieJar, self).get_dict(domain=domain, path=path)
        if names:
            return {k: v for k, v in d.items() if k in names}
        else:
            return d

    def get_header_string(self, *names, domain=None, path=None, header='Cookie: '):
        return header + '; '.join([f'{k}={v}' for k, v in self.get_dict(*names, domain=domain, path=path).items()])

    def select(self, *names):
        new = EzCookieJar()
        new.set_policy(self.get_policy())
        for c in self:
            if c.name in names:
                new.set_cookie(c)
        return new

    @staticmethod
    def convert_json_cookies_to_netscape_text(list_of_cookie_dict):
        lines = [NETSCAPE_HEADER_TEXT]
        for d in list_of_cookie_dict:
            c = SingleCookieDict(d)
            lines.append(c.get_netscape_line())
        return '\n'.join(lines)
