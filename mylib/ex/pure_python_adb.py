#!/usr/bin/env python3
import ppadb.client
import ppadb.command.host
import ppadb.device

from mylib.easy import *


class AndroidDevice(ppadb.device.Device):
    def input_roll(self, dx, dy):
        return self.shell(f'input roll {dx} {dy}')

    def input_swipe(self, x1, y1, x2, y2, seconds=None):
        return super().input_swipe(x1, y1, x2, y2, (int(seconds * 1000) if seconds is not None else ''))


ppadb.device.Device = ppadb.command.host.Device = AndroidDevice
ppadb.client.Host = ppadb.command.host.Host


class ADBClient(ppadb.client.Client):
    def connect(self, address: str):
        r = parse_host_port_address(address)
        return self.remote_connect(r.hostname, r.port or 5555)


ppadb.client.Client = ADBClient
