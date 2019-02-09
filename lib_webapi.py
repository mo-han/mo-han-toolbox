#!/usr/bin/env python
# -*- coding: utf-8 -*-

import lowendspirit


class SolusVMClientToolkit(lowendspirit.Solus_Enduser_API):
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
        super(SolusVMClientToolkit, self).__init__(self.api_host, self.api_host, self.api_key)

    def is_online(self):
        vmstat = self.get_status()['vmstat']
        if vmstat == 'online':
            return True
        elif vmstat == 'offline':
            return False
        else:
            raise ValueError('vmstat: {}'.format(vmstat))
