#!/usr/bin/env python3
from socket import *
from ..easy import ez_parse_netloc


def ez_parse_host_port(url):
    r = ez_parse_netloc(url)
    return r.hostname, r.port


class EzSocket(socket):
    address: tuple

    def set_netloc(self, url):
        r = ez_parse_netloc(url)
        self.address = r.hostname, r.port
        return self

    def set_host_port(self, host, port):
        self.address = host, port
        return self

    def connect(self, address=None):
        address = address or self.address
        super(EzSocket, self).connect(address)
        return self
