#!/usr/bin/env python3
import json
from http.cookiejar import CookieJar as InstalledCookieJar

from ezpykit.allinone import io, os, ezlist, ezstr, ctx_ensure_module
from ezpykit.stdlib.http.cookiejar import MozillaCookieJar, LoadError, CookieJar

with ctx_ensure_module('requests'):
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
            flag_true = 'TRUE'
            flag_false = 'FALSE'
            domain = f'#HttpOnly_{self["domain"]}' if self.get('httpOnly') else self['domain']
            include_subdomains = flag_false if self.get('hostOnly') else flag_true
            path = self['path']
            secure = flag_true if self['secure'] else flag_false
            expire = self.get('expirationDate', self.get('expires', self.get('expiry', 2 ^ 32 - 1)))
            name = self['name']
            value = self['value']
            return '\t'.join([domain, include_subdomains, path, secure, str(expire), name, value])
        except KeyError as e:
            raise self.InvalidCookieDict('missing key', *e.args)


class EzCookieJar(MozillaCookieJar, RequestsCookieJar):
    temp_vfname = f'virtualfile:///EzCookieJar.temp.txt'
    max_vfsize = 1024 * 1024 * 16

    @classmethod
    def is_cookiejar(cls, x):
        return isinstance(x, (InstalledCookieJar, CookieJar))

    def smart_load(self, source, ignore_discard=False, ignore_expires=False):
        common_kwargs = dict(ignore_discard=ignore_discard, ignore_expires=ignore_expires)
        if isinstance(source, list):
            return self.load_json_list(source, **common_kwargs)
        if os.is_path(source) and os.path_isfile(source):
            source = io.IOKit.read_exit(open(source))
        try:
            json.loads(source)
        except (json.JSONDecodeError, TypeError):
            is_json = False
        else:
            is_json = True
        if is_json:
            self.load_json(source, **common_kwargs)
        else:
            try:
                self.load_netscape(source, **common_kwargs)
            except LoadError:
                try:
                    self.load_string(source)
                except ValueError:
                    raise ValueError('failed to load', source)

    def load_string(self, source, **kwargs):
        if os.is_path(source) and os.path_isfile(source):
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
        if os.is_path(source) and os.path_isfile(source):
            source = io.IOKit.read_exit(open(source))
        j = json.loads(source)
        if isinstance(j, dict) and 'cookies' in j:
            j = j['cookies']
        if isinstance(j, list):
            return self.load_json_list(j, ignore_discard=ignore_discard, ignore_expires=ignore_expires)
        raise ValueError('invalid json source')

    def load_json_list(self, cookie_json_list, ignore_discard=False, ignore_expires=False):
        first = ezlist.get_first(cookie_json_list)
        if not first:
            return
        elif not isinstance(first, dict):
            raise TypeError('cookie dict', type(first))
        netscape_text = self.get_netscape_text_from_json_list(cookie_json_list)
        if len(netscape_text) > self.max_vfsize:
            raise RuntimeError('content too leng', self.max_vfsize, len(netscape_text))
        with io.ctx_open_virtualfileio():
            io.IOKit.write_exit(open(self.temp_vfname, 'w'), netscape_text)
            super().load(self.temp_vfname, ignore_discard=ignore_discard, ignore_expires=ignore_expires)
            return

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

    @staticmethod
    def get_netscape_text_from_json_list(cookie_json_list):
        lines = [NETSCAPE_HEADER_TEXT]
        for d in cookie_json_list:
            lines.append(SingleCookieDict(d).get_netscape_line())
        return '\n'.join(lines)

    def sel_dict(self, *names, domain=None, path=None):
        d = super(EzCookieJar, self).get_dict(domain=domain, path=path)
        if names:
            return {k: v for k, v in d.items() if k in names}
        else:
            return d

    def get_header_string(self, *names, domain=None, path=None, header='Cookie: '):
        return header + '; '.join([f'{k}={v}' for k, v in self.sel_dict(*names, domain=domain, path=path).items()])

    def select(self, *names):
        new = EzCookieJar()
        new.set_policy(self.get_policy())
        for c in self:
            if c.name in names:
                new.set_cookie(c)
        return new


def get_cookies_dict(source):
    if EzCookieJar.is_cookiejar(source):
        return EzCookieJar.get_dict(source)
    cj = EzCookieJar()
    cj.smart_load(source, ignore_expires=True, ignore_discard=True)
    return cj.get_dict()
