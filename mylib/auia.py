#!/usr/bin/env python3
# encoding=utf8
"""Android UI Automate"""
import uiautomator2
import ppadb.client


class AUIABase:
    def __init__(self, remote_addr: str):
        self._addr = remote_addr
        self._device =

    def adb_connect_remote(self, max_try):
