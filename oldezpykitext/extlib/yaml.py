#!/usr/bin/env python3
from oldezpykit.allinone import ctx_ensure_module, os

with ctx_ensure_module('yaml', 'PyYAML'):
    from yaml import *


class YAMLFile:
    default_encoding = 'utf8'

    def __init__(self, fp, auto_create_file=False):
        self.filepath = fp
        if auto_create_file and not os.path_isfile(fp):
            os.touch(fp)

    def load(self, load_method=safe_load, encoding=None, **kwargs):
        return load_method(open(self.filepath, encoding=encoding or self.default_encoding), **kwargs)

    def dump(self, data, dump_method=safe_dump, encoding=None, allow_unicode=True, **kwargs):
        if issubclass(type(data), dict):
            data = dict(data)
        return dump_method(
            data, open(self.filepath, 'w', encoding=encoding or self.default_encoding),
            allow_unicode=allow_unicode, **kwargs
        )
