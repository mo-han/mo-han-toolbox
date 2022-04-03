#!/usr/bin/env python3
from ezpykit.allinone import subprocess
from ezpykitext.webclient import *


class BBDownCommandLineList(subprocess.CommandLineList):
    which = 'BBDown'

    def _kwarg_to_option(self, key, value):
        if '_' in key:
            opt_name = '--' + '-'.join(key.split('_'))
        else:
            opt_name = '-' + key
        return opt_name, value

    def set_cookies(self, source):
        cj = cookies.EzCookieJar()
        cj.smart_load(source, ignore_expires=True)
        s = cj.get_header_string('SESSDATA', header='')
        return self.add(c=s)

    def get_info(self, uri):
        p = self.add(uri, info=True)
