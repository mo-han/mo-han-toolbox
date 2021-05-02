#!/usr/bin/env python3
from abc import ABC

from mylib.easy import *


class FilenameTagsABC(ABC):
    def __init__(self):
        self.tags_set = set()
        self.tags_dict = dict()
        self.config = {}

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

    def tagged_path(self):
        ...

    @property
    def path(self):
        return self.tagged_path()

    def untagged_path(self):
        ...

    @property
    def no_tag(self):
        return self.untagged_path()

    def __repr__(self):
        config_s = ', '.join([f'{k}={v}' for k, v in self.config.items()])
        return f'{self.__class__.__name__}(tags={self.tags}, filename={self.path}, {config_s})'

    def clear(self):
        """clear all tags from filename"""
        self.tags_dict.clear()
        self.tags_set.clear()
        return self

    def tag(self, *tags: str, **kw_tags: str):
        """add tag(s)"""
        self.tags_set.update(tags)
        self.tags_dict.update(kw_tags)
        return self

    def untag(self, *tags: str):
        """remove tag(s)"""
        self.tags_set.difference_update(tags)
        for k in set(self.tags_dict).intersection(tags):
            del self.tags_dict[k]
        return self


class SingleFilenameTags(FilenameTagsABC):
    def __init__(self, path: str, *, preamble='.', begin='[', end=']', sep=' '):
        super().__init__()
        self.config = dict(preamble=repr(preamble), begin=repr(begin), end=repr(end), sep=repr(sep))
        self.begin = begin
        self.begin_re = re.escape(begin)
        self.end = end
        self.end_re = re.escape(end)
        self.preamble = preamble
        self.preamble_re = re.escape(preamble)
        self.sep = sep
        tags_pattern = fr'{self.preamble_re}{self.begin_re}[^{self.begin_re}{self.end_re}]*{self.end_re}'
        # print(tags_pattern)
        parent_dir, body, ext = split_path_dir_base_ext(path)
        if re.search(tags_pattern, ext):
            body += ext
            ext = ''
        self.extension = ext
        try:
            before_tags, the_tags, after_tags = re.split(fr'({tags_pattern})', body, maxsplit=1)
            # print(before_tags, the_tags, after_tags)
            tags_s = str(the_tags[len(self.preamble) + len(self.begin):-len(self.end)]).strip()
            tags_l = tags_s.split(sep) if tags_s else []
        except ValueError:
            before_tags = body
            after_tags = ''
            tags_l = []
        self.before_tags = os.path.join(parent_dir, before_tags)
        self.after_tags = after_tags
        for t in tags_l:
            if '=' in t:
                k, v = t.split('=', maxsplit=1)
                self.tags_dict[k] = v
            else:
                self.tags_set.add(t)

    def tagged_path(self):
        tags_l = sorted(self.tags)
        if tags_l:
            return f'{self.before_tags}{self.preamble}{self.begin}{self.sep.join(tags_l)}{self.end}{self.after_tags}{self.extension}'
        else:
            return f'{self.before_tags}{self.after_tags}{self.extension}'

    def untagged_path(self):
        return f'{self.before_tags}{self.after_tags}{self.extension}'
