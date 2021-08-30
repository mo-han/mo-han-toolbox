#!/usr/bin/env python3
import lxml.html as lxml_html
import requests as requests

from mylib import easy


class ResponseError(Exception):
    pass


class HTMLResponseParser:
    def __init__(self, response=requests.Response):
        self._response = response

    @property
    def response(self):
        return self._response

    @property
    def r(self):
        return self._response

    @property
    def ok(self):
        return self.r.ok

    def check_ok_or_raise(self):
        if not self.ok:
            raise ResponseError(self.r)
        return self

    @easy.functools.lru_cache()
    def get_html_element(self) -> lxml_html.HtmlElement:
        return lxml_html.fromstring(self.r.text)
