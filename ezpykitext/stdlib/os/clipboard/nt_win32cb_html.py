#!/usr/bin/env python3
# modified from file `HTMLClipboard.py`
import re

from ezpykit.metautil import deco_ctx_with_self
from ezpykitext.extlib.win32clipboard import *


class HTMLClipboardMixin:
    MARKER_BLOCK_OUTPUT = (
        'Version:1.0\r\n'
        'StartHTML:%09d\r\n'
        'EndHTML:%09d\r\n'
        'StartFragment:%09d\r\n'
        'EndFragment:%09d\r\n'
        'StartSelection:%09d\r\n'
        'EndSelection:%09d\r\n'
        'SourceURL:%s\r\n'
    )

    MARKER_BLOCK_EX_RE = re.compile((
        r'Version:(\S+)\s+'
        r'StartHTML:(\d+)\s+'
        r'EndHTML:(\d+)\s+'
        r'StartFragment:(\d+)\s+'
        r'EndFragment:(\d+)\s+'
        r'StartSelection:(\d+)\s+'
        r'EndSelection:(\d+)\s+'
        r'SourceURL:(\S+)'
    ))

    MARKER_BLOCK_RE = re.compile((
        r'Version:(\S+)\s+'
        r'StartHTML:(\d+)\s+'
        r'EndHTML:(\d+)\s+'
        r'StartFragment:(\d+)\s+'
        r'EndFragment:(\d+)\s+'
        r'SourceURL:(\S+)'
    ))

    DEFAULT_HTML_BODY = (
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">'
        '<HTML><HEAD></HEAD><BODY><!--StartFragment-->%s<!--EndFragment--></BODY></HTML>'
    )

    CF_HTML = None
    html = None
    html_fragment = None
    html_selection = None
    html_source_url = None
    html_clipboard_version = None

    def _get_cf_html(self):
        if self.CF_HTML is None:
            self.CF_HTML = RegisterClipboardFormat('HTML Format')
        return self.CF_HTML

    @deco_ctx_with_self
    def _get_available_formats(self):
        formats = []
        while True:
            cf = EnumClipboardFormats()
            if cf == 0:
                break
            formats.append(cf)
        return formats

    def has_html(self):
        return self._get_cf_html() in self._get_available_formats()

    @deco_ctx_with_self
    def _read_html(self):
        src = GetClipboardData(self._get_cf_html())
        src = src.decode('u8')
        matches = self.MARKER_BLOCK_EX_RE.match(src)
        if matches:
            self.html_clipboard_version = matches.group(1)
            self.html = src[int(matches.group(2)):int(matches.group(3))]
            self.html_fragment = src[int(matches.group(4)):int(matches.group(5))]
            self.html_selection = src[int(matches.group(6)):int(matches.group(7))]
            self.html_source_url = matches.group(8)
        else:
            # Failing that, try the version without a selection
            matches = self.MARKER_BLOCK_RE.match(src)
            if matches:
                self.html_prefix = matches.group(0)
                self.html_clipboard_version = matches.group(1)
                self.html = src[int(matches.group(2)):int(matches.group(3))]
                self.html_fragment = src[int(matches.group(4)):int(matches.group(5))]
                self.html_source_url = matches.group(6)
                self.html_selection = self.html_fragment

    def get_html(self, refresh=True):
        if not self.html or refresh:
            self._read_html()
        return self.html

    def set_html(self, html_fragment, selection=None, html=None, source_url=None):
        if selection is None:
            selection = html_fragment
        if html is None:
            html = self.DEFAULT_HTML_BODY % html_fragment
        if source_url is None:
            source_url = __file__
        frag_start = html.index(html_fragment)
        frag_end = frag_start + len(html_fragment)
        sel_start = html.index(selection)
        sel_end = sel_start + len(selection)
        self._write_html(html, frag_start, frag_end, sel_start, sel_end, source_url)

    @deco_ctx_with_self
    def _write_html(self, html, fragment_start, fragment_end, selection_start, selection_end, source_url=__file__):
        EmptyClipboard()
        prefix_dummy = self.MARKER_BLOCK_OUTPUT % (0, 0, 0, 0, 0, 0, source_url)
        prefix_len = len(prefix_dummy)
        prefix = self.MARKER_BLOCK_OUTPUT % (prefix_len, len(html) + prefix_len,
                                             fragment_start + prefix_len, fragment_end + prefix_len,
                                             selection_start + prefix_len, selection_end + prefix_len,
                                             source_url)
        src = (prefix + html)
        src = src.encode('u8')
        SetClipboardData(self._get_cf_html(), src)
