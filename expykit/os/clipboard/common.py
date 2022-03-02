#!/usr/bin/env python3
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from ezpykit.call import SimpleCall


class ClipboardABC(ABC):
    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def set(self, data):
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def get_path(self, exist_only=True) -> list:
        pass

    @abstractmethod
    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def url_api(self, url: str):
        slash = '/'
        calling_map = {
            'get': SimpleCall(self.get),
            'get/path': SimpleCall(self.get_path),
        }

        pr = urlparse(url)
        if pr.scheme not in ('clip', 'clipboard'):
            raise ValueError('invalid scheme', pr.scheme)
        if pr.netloc not in ('', 'localhost'):
            raise NotImplementedError('remote clipboard')
        if pr.params or pr.query:
            raise NotImplementedError('URL parameters & query string')
        entry = pr.path.strip(slash)
        if entry in calling_map:
            c: SimpleCall = calling_map[entry]
            return c.run()
        else:
            raise NotImplementedError('URL path entry', entry)
