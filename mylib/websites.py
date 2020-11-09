#!/usr/bin/env python3
# encoding=utf8

import requests


def get_cloudflare_ipaddr_hostmonit(key="o1zrmHAF"):
    # https://github.com/ddgth/cf2dns/blob/master/cf2dns.py
    url = 'https://api.hostmonit.com/get_optimization_ip'
    r = requests.post(url, json={"key": key}, headers={'Content-Type': 'application/json'})
    return r.json()
