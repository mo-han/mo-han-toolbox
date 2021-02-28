#!/usr/bin/env python3
# encoding=utf8
import requests_html as rqh
from mylib.traitsui_ez.i1_add_traits import *
from mylib.web_client import parse_https_url

HOST = 'hentai.cafe'
URL_ROOT = f'https://{HOST}'

__logger__ = get_logger(f'sites.{__name__}')


class HentaiCafeURL(Regex):
    def __init__(self, value='', **metadata):
        regex = r'(https://)?hentai\.cafe/.+|/hc\.fyi/.+'
        super(Regex, self).__init__(value=value, regex=regex, **metadata)

    def validate(self, obj, name, value):
        v = super(HentaiCafeURL, self).validate(obj, name, value)
        p = parse_https_url(v)
        if p.netloc == HOST:
            return p.geturl()
        if p.path.startswith('/hc.fyi/'):
            p = p._replace(netloc=HOST)
            return p.geturl()
        self.error(obj, name, value)

    @staticmethod
    def info():
        return "a `str` of hentai.cafe URL like 'https://hentai.cafe/hc.fyi/***' or just the path '/hc.fyi/***'"


class HentaiCafeItem(HasTraits):
    url = HentaiCafeURL
    data = Dict

    html_parser: rqh.HTML
    headers: dict = {}
    cookies: dict = {}
    more_requests_kwargs: dict = {}

    def __init__(self, url, headers: dict = None, cookies: dict = None, more_requests_kwargs: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.more_requests_kwargs = more_requests_kwargs or {}
        self.update_html_parser()

    def make_requests_kwargs(self):
        return dict(headers=self.headers, cookies=self.cookies, **self.more_requests_kwargs)

    def update_html_parser(self):
        self.html_parser = rqh.HTMLSession().get(self.url, **self.make_requests_kwargs()).html

    def _url_changed(self, new):
        d = {'site': HOST, 'url': new}
        has_children = has_chapters = False

        p = parse_https_url(new)
        path = p.path
        query = p.query

        hc_fyi = '/hc.fyi/'
        qs = 's='
        if path.startswith(hc_fyi):
            follow_hc_fyi = str_remove_prefix(path, hc_fyi)
            try:
                d['manga_id'] = d['id'] = int(follow_hc_fyi)
                has_chapters = True
            except ValueError:
                for p in ('tag', 'artist', 'category'):
                    if follow_hc_fyi.startswith(f'{p}/'):
                        has_children = True
                        break
        elif query.startswith(qs):
            search = str_remove_prefix(query, qs)
            d['search'] = search
            has_children = True
        elif path == '':
            has_children = True
        else:
            __logger__.warning('unknown URL path of hentai.cafe')

        self.update_html_parser()

        if has_children:
            d['children'] = get_manga_url_iter(self.html_parser, **self.make_requests_kwargs())

        self.data = d


def get_manga_url_iter(url_or_html: str or rqh.HTML, auto_next_page=True, **requests_kwargs):
    if isinstance(url_or_html, str):
        html_parser: rqh.HTML = rqh.HTMLSession().get(url_or_html, **requests_kwargs).html
    else:
        html_parser: rqh.HTML = url_or_html
    yield from [e.attrs['href'] for e in html_parser.find('.entry-wrap a')]
    if not auto_next_page:
        return
    pages = html_parser.find('span.pages', first=True)
    if not pages:
        return
    current, total = [int(x) for x in re.search(r'Page (\d+) of (\d+)', pages.text).groups()]
    if current >= total:
        return
    p = parse_https_url(html_parser.url)
    new_url = p._replace(path=f'{p.path.split("/page/")[0]}/page/{current + 1}').geturl()
    yield from get_manga_url_iter(new_url, auto_next_page=auto_next_page, **requests_kwargs)
