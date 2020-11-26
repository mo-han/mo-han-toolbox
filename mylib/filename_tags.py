#!/usr/bin/env python3
# encoding=utf8
import os
import re
from abc import ABC

from .os_auto import split_filename


class ListFilenameTags(ABC):
    def __init__(self):
        self.tags_set = set()
        self.tags_dict = dict()

    @property
    def tags(self) -> set:
        return self.tags_set.union([f'{k}={v}' for k, v in self.tags_dict.items()])

    @property
    def keys(self) -> set:
        return self.tags_set.union(self.tags_dict.keys())

    def get_path(self):
        ...

    @property
    def path(self):
        return self.get_path()

    def __repr__(self):
        return f'{self.__class__.__name__}(tags={self.tags}, filename={self.path})'

    def clear(self):
        """clear all tags from filename"""
        self.tags_dict.clear()
        self.tags_set.clear()
        return self

    def tag(self, *tags, **kw_tags):
        """add tag(s)"""
        self.tags_set.update(tags)
        self.tags_dict.update(kw_tags)
        return self

    def untag(self, *tags):
        """remove tag(s)"""
        self.tags_set.difference_update(tags)
        for k in set(self.tags_dict).intersection(tags):
            del self.tags_dict[k]
        return self


class SuffixListFilenameTags(ListFilenameTags):
    def __init__(self, path: str, *, left='.[', right=']', sep=' '):
        super().__init__()
        self.left = left
        self.right = right
        self.sep = sep
        tags_pattern = f'({re.escape(self.left)}.*{re.escape(self.right)})$'
        if re.search(tags_pattern, path):
            pd, fn = os.path.split(path)
            ext = ''
        else:
            pd, fn, ext = split_filename(path)
        parts = re.split(tags_pattern, fn)
        self.prefix = os.path.join(pd, parts[0])
        self.extension = ext
        if len(parts) > 1:
            tags_s = parts[1].lstrip(self.left).rstrip(self.right).strip()
        else:
            tags_s = ''
        if tags_s:
            tags_l = tags_s.split(sep=sep)
        else:
            tags_l = []
        for t in tags_l:
            if '=' in t:
                k, v = t.split('=', maxsplit=1)
                self.tags_dict[k] = v
            else:
                self.tags_set.add(t)

    def get_path(self):
        tags_l = sorted(self.tags)
        if tags_l:
            return f'{self.prefix}{self.left}{self.sep.join(tags_l)}{self.right}{self.extension}'
        else:
            return f'{self.prefix}{self.extension}'
