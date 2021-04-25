#!/usr/bin/env python3

import requests_html
from qtpy.QtCore import QUrl
from qtpy.QtWebEngineWidgets import QWebEnginePage
from qtpy.QtWidgets import QApplication

from mylib.easy import *


@deco_cached_call
def get_qt_application_singleton(klass=QApplication, argv=None):
    argv = argv or sys.argv
    return klass(argv)


class QtWebPageRender:
    url: str
    html_str: str
    html_parser: requests_html.HTML

    def __init__(self, qt_app_singleton=None):
        self._qt_app = qt_app_singleton or get_qt_application_singleton()
        self._qt_webpage = QWebEnginePage()
        self._qt_webpage.loadFinished.connect(self._on_load_finished)

    def _on_load_finished(self):
        self._qt_webpage.toHtml(self._update_html)

    def _update_html(self, qt_webpage_to_html: str):
        self.html_str = qt_webpage_to_html
        self.html_parser = requests_html.HTML(url=self.url, html=self.html_str)
        self.find = self.html_parser.find
        self.xpath = self.html_parser.xpath
        self._qt_app.quit()

    def set_url(self, url: str):
        self.url = url
        self._qt_webpage.load(QUrl(url))
        self._qt_app.exec_()

    def set_html(self, html: str, base_url: str = ''):
        self.url = base_url
        self._qt_webpage.setHtml(html, QUrl(base_url))
        self._qt_app.exec_()

    @property
    def text(self):
        return self.html_parser.text
