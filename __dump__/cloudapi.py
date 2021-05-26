#!/usr/bin/env python
# -*- coding: utf-8 -*-

import lowendspirit
import hurry.filesize
from time import sleep
import os


class SolusVMClientAPI(lowendspirit.Solus_Enduser_API):
    """SolusVM client panel API for virtual server instance, a wrapper of `lowendspirit.Solus_Enduser_API`."""
    KNOWN_HOSTS = {
        'alpharacks': 'vpscp.alpharacks.com',
        'virmach': 'solusvm.virmach.com',
    }

    def __init__(self, api_host: str, api_key: str, api_hash: str):
        if api_host in self.KNOWN_HOSTS:
            self.api_host = self.KNOWN_HOSTS[api_host]
        else:
            self.api_host = api_host
        self.api_key = api_key
        self.api_hash = api_hash
        super(SolusVMClientAPI, self).__init__(self.api_host, self.api_hash, self.api_key)

    @property
    def online(self) -> bool:
        vmstat = self.get_status()['vmstat']
        if vmstat == 'online':
            return True
        elif vmstat == 'offline':
            return False
        else:
            raise RuntimeError('vmstat: {}'.format(vmstat))

    def usage(self, sth: str, convert: bool = False) -> tuple:
        """Get usage information, data given in tuple of `int` by bytes, or given as tuple of converted `str`.

        :param sth: str, usage of sth, 'bw' for bandwidth, 'hdd' for disk, 'mem' for memory, etc.
        :param convert: bool, if `True`, convert usage from bytes to `str` in KiB, MiB, GiB, etc. automatically.
        :return tuple(total, used, avail, used_pct), in bytes by default, except `used_pct` (percentage).
        """
        full_info = self.get_full_info()
        total, used, avail, used_pct = tuple(int(s) for s in full_info[sth].split(','))
        if convert:
            size = hurry.filesize.size
            # iec = hurry.filesize.iec
            iec = [(1125899906842624, ' PiB'), (1099511627776, ' TiB'), (1073741824, ' GiB'), (1048576, ' MiB'),
                   (1024, ' KiB'), (1, (' Byte', ' Bytes'))]
            total = size(total, system=iec)
            used = size(used, system=iec)
            avail = size(avail, system=iec)
            used_pct = '{}%'.format(used_pct)
        return total, used, avail, used_pct

    def bw(self, convert=False) -> tuple:
        """Usage of bandwidth cap, see `usage()` for details."""
        return self.usage('bw', convert)

    def disk(self, convert=False) -> tuple:
        """Usage of disk space, see `usage()` for details."""
        return self.usage('hdd', convert)

    hdd = disk

    def mem(self, convert=False) -> tuple:
        """Usage of memory, see `usage()` for details."""
        return self.usage('mem', convert)

    @property
    def ip(self) -> str:
        return self.get_info()['ipaddress']

    boot = lowendspirit.Solus_Enduser_API.server_boot
    shutdown = lowendspirit.Solus_Enduser_API.server_shutdown
    reboot = lowendspirit.Solus_Enduser_API.server_reboot


class SolusVMClientToolkit:
    def __init__(self, svr: SolusVMClientAPI):
        self.svr = svr

    def reboot_if_offline(self):
        if not self.svr.online:
            self.svr.shutdown()
            self.svr.boot()

    def ping(self, count=3):
        if os.name == 'nt':
            cmd = 'ping -n {} {}'
        else:
            cmd = 'ping -c {} {}'
        cmd = cmd.format(count, self.svr.ip)
        ec = os.system(cmd)
        if ec:
            return False
        else:
            return True

    def keep_online(self, nap: float = 300, by_ping: bool = True):
        while True:
            if by_ping:
                if self.ping():
                    self.reboot_if_offline()
            else:
                self.reboot_if_offline()
            sleep(nap)
