#!/usr/bin/env python3
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from ezpykit.builtin import ensure_str
from ezpykit.wip.call import SimpleCall


class ClipboardError(Exception):
    pass


class ClipboardURIError(ClipboardError):
    pass


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

    def get_lines(self):
        return self.get().splitlines()

    def resolve_uri(self, uri: str) -> SimpleCall:
        uri = ensure_str(uri)
        slash = '/'
        calling_map = {
            'get': SimpleCall(self.get),
            'get/path': SimpleCall(self.get_path),
            'get/lines': SimpleCall(self.get_lines),
            'set': SimpleCall(self.set)
        }

        pr = urlparse(uri)
        if pr.scheme not in ('clip', 'clipboard'):
            raise ClipboardURIError('invalid scheme', pr.scheme)
        if pr.netloc not in ('', 'localhost'):
            raise NotImplementedError('remote clipboard')
        if pr.params or pr.query:
            raise NotImplementedError('URL parameters & query string')
        entry = pr.path.strip(slash)
        if entry in calling_map:
            return calling_map[entry]
        else:
            raise NotImplementedError('URI path entry', entry)

    def check_uri(self, uri: str):
        uri = ensure_str(uri)
        try:
            if self.resolve_uri(uri):
                return True
        except (ClipboardURIError, NotImplementedError):
            return False

    def uri_api(self, uri: str, *args, **kwargs):
        call = self.resolve_uri(uri)
        if args or kwargs:
            call.args = args
            call.kwargs = kwargs
        return call.run()
