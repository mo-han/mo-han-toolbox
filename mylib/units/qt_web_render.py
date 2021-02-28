#!/usr/bin/env python3
# encoding=utf8
from PySide2.QtCore import QUrl
from PySide2.QtWebEngineWidgets import QWebEnginePage
from PySide2.QtWidgets import QApplication
from requests_html import HTML


class QtWebPageRender(QWebEnginePage):
    html: str
    url: str
    html_parser: HTML

    def __init__(self, qt_app: QApplication):
        self.app = qt_app
        QWebEnginePage.__init__(self)
        self.loadFinished.connect(self._on_load_finished)
        self.xpath = self.html_parser.xpath
        self.find = self.html_parser.find

    @property
    def text(self):
        return self.html_parser.text

    def set_url(self, url: str):
        self.url = url
        self.load(QUrl(url))
        self.app.exec_()

    def set_html(self, html: str, base_url: str = ''):
        self.url = base_url
        self.setHtml(html, QUrl(base_url))
        self.app.exec_()

    def _on_load_finished(self):
        self.toHtml(self._update_html)

    def _update_html(self, html: str):
        self.html = html
        self.html_parser = HTML(url=self.url, html=self.html)
        self.app.quit()
