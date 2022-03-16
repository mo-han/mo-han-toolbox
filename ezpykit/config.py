#!/usr/bin/env python3
import os
from abc import ABC, abstractmethod

from ezpykit.builtin import ezlist, ezdict
from ezpykit.allinone import T
from ezpykit.stdlib.urllib.parse import tolerant_urlparse


class ConfigABC(ABC):
    broad_default = True
    data: T.Mapping

    def __getitem__(self, key):
        keys = self.keys_sequence_of_search(key)
        for k in keys:
            if k in self.data:
                return self.data[k]
        raise KeyError(key)

    def __contains__(self, key):
        keys = self.keys_sequence_of_search(key)
        for k in keys:
            if k in self.data:
                return True
        return False

    def get(self, key, default=None):
        return self[key] if key in self else default

    @abstractmethod
    def keys_sequence_of_search(self, key) -> list:
        ...


class EnVarConfig(ConfigABC):
    sep = '_'
    uppercase_only = False
    convert_value = True

    def __init__(self):
        self.data = os.environ

    def __getitem__(self, key):
        v = super().__getitem__(key)
        return self.auto_convert(v) if self.convert_value else v

    def keys_sequence_of_search(self, key) -> list:
        keys = ezlist()

        def _add_key(k):
            if not self.uppercase_only:
                keys.append_dedup(k)
            keys.append_dedup(k.upper())

        if isinstance(key, list):
            _add_key(self.sep.join(key))
            if self.broad_default:
                _add_key(key[-1])
        elif isinstance(key, str):
            _add_key(key)
        else:
            raise TypeError('key', (list, str), type(key))
        return keys

    @staticmethod
    def auto_convert(s: str):
        for f in (int, float):
            try:
                return f(s)
            except ValueError:
                continue
        return s

    def get_proxy(self):
        def _to_dict(proxy_value):
            r = tolerant_urlparse(proxy_value)
            return dict(url=proxy_value, hostname=r.hostname, port=r.port, urlparse=r)

        http_proxy = self.get('http_proxy')
        https_proxy = self.get('https_proxy')
        proxies = {}
        if http_proxy:
            proxies['http'] = _to_dict(http_proxy)
        if https_proxy:
            proxies['https'] = _to_dict(https_proxy)
        return proxies


class DictConfig(ConfigABC):
    data: ezdict

    def set_data(self, x):
        if not isinstance(x, T.Mapping):
            raise TypeError('x', T.Mapping, type(x))
        self.data = ezdict(x)
        return self

    def keys_sequence_of_search(self, key) -> list:
        if isinstance(key, list):
            if self.broad_default:
                return [key, key[-1]]
            else:
                return [key]
        elif isinstance(key, str):
            return [key]
        else:
            raise TypeError('key', (list, str), type(key))
