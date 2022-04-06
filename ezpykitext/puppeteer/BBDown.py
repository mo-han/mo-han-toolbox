#!/usr/bin/env python3
from ezpykit.allinone import subprocess
from ezpykitext.webclient import *


class BBDownCommandLineList(subprocess.CommandLineList):
    which = 'BBDown'
    enable_short_option_for_word = True

    def set_cookies(self, source):
        cj = cookies.EzCookieJar()
        cj.smart_load(source, ignore_expires=True)
        s = cj.get_header_string('SESSDATA', header='')
        return self.add(c=s)

    def get_info(self, uri):
        p = self.add(uri, info=True)
