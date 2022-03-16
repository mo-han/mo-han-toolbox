#!/usr/bin/env python3
from ezpykit.allinone import os

try:
    import requests.cookies as ___
except ImportError:
    if os.system('pip install requests'):
        raise ImportError('failed to install', 'requests')

from requests.structures import CaseInsensitiveDict


class UserAgentExamples:
    """https://www.networkinghowtos.com/howto/common-user-agent-list/"""
    GOOGLE_CHROME_WINDOWS = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    GOOGLE_CHROME_ANDROID = 'Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.82 Mobile Safari/537.36'
    MOZILLA_FIREFOX_WINDOWS = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0'
    MOZILLA_FIREFOX_ANDROID = 'Mozilla/5.0 (Android 11; Mobile) Gecko/88.0 Firefox/88.0'
    MICROSOFT_EDGE = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393'
    APPLE_IPAD = 'Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4'
    APPLE_IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
    GOOGLE_BOT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    BING_BOT = 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)'
    CURL = 'curl/7.35.0'
    WGET = 'Wget'
    LYNX = 'Lynx'


class EzHeaders(CaseInsensitiveDict):
    def set_user_agent(self, ua=UserAgentExamples.MOZILLA_FIREFOX_WINDOWS):
        self['User-Agent'] = ua
        return self

    set_ua = set_user_agent
