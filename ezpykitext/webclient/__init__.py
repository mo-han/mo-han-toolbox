#!/usr/bin/env python3
from ezpykit.allinone import ctx_ensure_module
from ezpykitext.webclient import browser
from ezpykitext.webclient import cookie
from ezpykitext.webclient import header
from ezpykitext.webclient import lxml_html

with ctx_ensure_module('requests'):
    import requests

___ref = [requests]
