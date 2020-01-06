#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Library for website operation"""

import splinter
import os

from lib_base import TEMPDIR

USER_AGENT_FIREFOX_WIN10 = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0'


class DownloadFailure(Exception):
    pass


def new_phantomjs() -> splinter.Browser:
    b = splinter.Browser(
        'phantomjs',
        user_agent=USER_AGENT_FIREFOX_WIN10,
        service_args=['--webdriver-loglevel=WARN'],
        service_log_path=os.path.join(TEMPDIR, 'ghostdriver.log'),
    )
    b.driver.set_window_size(800, 600)
    return b


def try_dl_file(url: str, max_retries: int = 3) -> tuple:
    pass
