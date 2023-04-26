#!/usr/bin/env python3
from oldezpykit.allinone import ctx_ensure_module
from oldezpykitext.webclient import browser
from oldezpykitext.webclient import cookie
from oldezpykitext.webclient import header
from oldezpykitext.webclient import lxml_html

with ctx_ensure_module('requests'):
    import requests

___ref = [requests]
