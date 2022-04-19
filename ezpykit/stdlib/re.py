#!/usr/bin/env python3
from re import *
from re import __doc__

from ezpykit.builtin import ezdict
from ezpykit.metautil import T, DummyObject

___ref = [__doc__]


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
        self.type = types

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

    def groups_dict(self, *names, **names_with_default):
        r = {}
        i = 0
        r[i] = self.group(i)
        for g in self.groups():
            i += 1
            r[i] = g
        r.update(self.groupdict())
        if names or names_with_default:
            r = ezdict.pick(r, *names, **names_with_default)
        return r


class BatchMatchWrapper:
    def __init__(self, *matches: T.Match):
        self.matches = matches

    def first_match(self):
        for m in self.matches:
            if m:
                return MatchWrapper(m)
