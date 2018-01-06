#!/usr/bin/env python3

import re
import bs4
import requests

def url_split(url: str):
    url_server = url.split['://']
    if len(url_server) >= 2:
        url_server = url_server[-1]
    url_server, url_dir = 