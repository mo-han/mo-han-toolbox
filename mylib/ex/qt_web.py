#!/usr/bin/env python3
"""NOT USABLE"""
from PySide2.QtWebEngineWidgets import *


class WebView(QWebEngineView):
    def __init__(self, parent=None, *, private_aka_incognito_mode=True):
        super(WebView, self).__init__(parent)
        profile = QWebEngineProfile('private') if private_aka_incognito_mode else QWebEngineProfile.defaultProfile()
        page = QWebEnginePage(profile)
        self.setPage(page)
