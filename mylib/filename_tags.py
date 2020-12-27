#!/usr/bin/env python3
# encoding=utf8
import os
import re
from abc import ABC

from . import fs


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

    def has_tag(self, *tag, **kw):
        tag_n = len(tag)
        kw_n = len(kw)
        if tag_n + kw_n > 1:
            raise ValueError('too many tags given (only one expected)')
        if tag_n:
            tag = tag[0]
            return tag in self.tags or tag in self.keys
        if kw_n:
            for k, v in kw.items():
                if v == '':
                    return k in self.tags or k in self.keys
                else:
                    return str(self.tags_dict.get(k)) == str(v)

    def get_path(self):
        ...

    @property
    def path(self):
        return self.get_path()

    def get_untagged_path(self):
        ...

    @property
    def notag(self):
        return self.get_untagged_path()

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
        tags_pattern = fr'{re.escape(left)}[^\[\]]*{re.escape(right)}'
        dn, bn, ext = fs.split_dirname_basename_ext(path)
        if re.search(tags_pattern, ext):
            bn += ext
            ext = ''
        self.extension = ext
        try:
            head, tags, _ = re.split(fr'({tags_pattern})$', bn)
            tags_s = str(tags[len(left):-len(right)]).strip()
            tags_l = tags_s.split(sep) if tags_s else []
        except ValueError:
            head = bn
            tags_l = []
        self.prefix = os.path.join(dn, head)
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

    def get_untagged_path(self):
        return f'{self.prefix}{self.extension}'
