#!/usr/bin/env python3
# encoding=utf8
"""Android UI Automate"""
import uiautomator2
import ppadb.client


class RemoteAndroidUI:
    def __init__(self):
        self._adb = ppadb.client.Client()
        self._devices_dict = {}
        self.get_devices()
        self._remote_ui: uiautomator2.Device or None = None

    @property
    def adb(self):
        return self._adb

    @property
    def devices(self):
        return self._devices_dict

    @property
    def remote_ui(self):
        return self._remote_ui

    def get_devices(self) -> dict:
        d = {}
        for device in self.adb.devices():
            d[device.serial] = device
        self._devices_dict = d
        return d

    def add_remote(self, addr: str) -> bool:
        host, port = addr.split(':', maxsplit=1)
        ok = self.adb.remote_connect(host, int(port))
        if ok:
            self.get_devices()
        return ok

    def sel_remote_ui(self, addr: str) -> bool:
        if addr not in self.devices:
            if not self.add_remote(addr):
                return False
        self._remote_ui = uiautomator2.connect(addr)
        return True

    def click_object(self, prop: str, value: str, timeout=None, offset=None) -> bool:
        if self.remote_ui is None:
            return False
        uio = self.find_object(prop, value)
        if uio:
            try:
                uio.click(timeout=timeout, offset=offset)
                return True
            except uiautomator2.exceptions.UiObjectNotFoundError:
                return False
        else:
            return False

    def find_object(self, prop: str, value: str, timeout=None) -> uiautomator2.UiObject or None:
        if self.remote_ui is None:
            return None
        uio = self.remote_ui(**{prop: value})
        try:
            uio.must_wait(timeout=timeout)
            return uio
        except uiautomator2.exceptions.UiObjectNotFoundError:
            return None
