#!/usr/bin/env python3
from re import *
from re import __doc__

from oldezpykit.metautil import T, DummyObject

___ref = [__doc__]

Match = type(match('', ''))
Pattern = type(compile(''))


def find_words(s: str, allow_mix_non_word_chars='\''):
    if allow_mix_non_word_chars is True:
        return [p for p in s.split() if search(r'\w', p)]
    elif allow_mix_non_word_chars:
        pattern = fr'[\w{escape(allow_mix_non_word_chars)}]+'
        return [p.strip() for p in findall(pattern, s)]
    else:
        return findall(r'\w+', s)


def simple_replace(s, pattern: str, repl: str, *, use_regex=False, ignore_case=False):
    if use_regex:
        if ignore_case:
            return sub(pattern, repl, s, flags=IGNORECASE)
        else:
            return sub(pattern, repl, s)
    else:
        if ignore_case:
            return sub(escape(pattern), escape(repl), s, flags=IGNORECASE)
        else:
            return s.replace(pattern, repl)


class MatchWrapper:
    DUMMY_MATCH = DummyObject(match('', ''), group=None)

    def __init__(self, m: T.Match, types: T.Iterable[type] = ()):
        self.match = m or self.DUMMY_MATCH
        self.types = types

    def convert_type(self, x):
        for t in self.types:
            try:
                return t(x)
            except:
                pass
        return x

    @property
    def named_groups(self):
        return self.match.groupdict()

    def __getattr__(self, item):
        return getattr(self.match, item)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            name, default = item
            try:
                return self.match[name]
            except IndexError:
                return default
        return self.match[item]

    def __repr__(self):
        return f'{self.__class__.__name__} of {self.match!r}'

    def group_dict(self):
        r = {i: self.convert_type(gv) for i, gv in enumerate(self.groups(), start=1)}
        r[0] = self.convert_type(self.group(0)),
        r.update({k: self.convert_type(v) for k, v in self.groupdict().items()})
        return r

    def pick_group_dict(self, *index_or_names, **names_with_default):
        r = {}
        for i in index_or_names:
            try:
                r[i] = self.convert_type(self.group(i))
            except IndexError:
                pass
        gd = self.groupdict()
        for n, d in names_with_default.items():
            if n in gd:
                r[n] = self.convert_type(gd[n])
            else:
                r[n] = self.convert_type(d)
        return r

    def pick_existing_group_dict(self, *index_or_names, **names_with_default):
        r = {}
        for i in index_or_names:
            try:
                v = self.convert_type(self.group(i))
                if v is not None:
                    r[i] = self.convert_type(self.group(i))
            except IndexError:
                pass
        gd = self.groupdict()
        for n, d in names_with_default.items():
            if n in gd and gd[n] is not None:
                r[n] = self.convert_type(gd[n])
            else:
                r[n] = self.convert_type(d)
        return r


class BatchMatchWrapper:
    def __init__(self, *pattern_or_match, string=None, types: T.Iterable[type] = ()):
        self.sequence = pattern_or_match
        self.string = string
        self.types = types

    def first_match(self):
        for x in self.sequence:
            if isinstance(x, Pattern):
                x = x.match(self.string)
            if isinstance(x, Match):
                return MatchWrapper(x, types=self.types)
