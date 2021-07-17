#!/usr/bin/env python3
from mylib.ex.html import *


def get_cloudflare_ipaddr_hostmonit(key="o1zrmHAF"):
    # https://github.com/ddgth/cf2dns/blob/master/cf2dns.py
    url = 'https://api.hostmonit.com/get_optimization_ip'
    r = requests.post(url, json={"key": key}, headers={'Content-Type': 'application/json'})
    return r.json()


def free_ss_site_vmess_uuid():
    r = requests.get('https://free-ss.site/')
    for e in lxml_html.fromstring(r.text).cssselect('script'):
        s = e.text
        if s and 'www.kernels.bid' in s:
            return easy.re.findall(easy.REGEX_GUID, s)[0]
