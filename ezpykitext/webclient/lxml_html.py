#!/usr/bin/env python3
from lxml.html import *
from lxml.html import HtmlElement, InputElement, TextareaElement
from ezpykit.metautil import hasattr_batch

__ref = Element, InputElement, TextareaElement


def html_etree_from(x, **kwargs) -> HtmlElement:
    if hasattr_batch(x, ('url', 'status_code', 'ok', 'request', 'content', 'text')):
        x = x.text
    if not isinstance(x, (str, bytes)):
        raise TypeError('x is not or does not contain string (str, bytes)', type(x))
    return document_fromstring(x, **kwargs)


def e_is_null(e):
    return e is None
