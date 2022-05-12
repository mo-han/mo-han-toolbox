#!/usr/bin/env python3
from ezpykit.allinone import *

with ctx_ensure_module('yaml', 'PyYAML'):
    from yaml import *


class YAMLFile:
    default_encoding = 'utf8'

    def __init__(self, fp, auto_create_file=False):
        self.filepath = fp
        if auto_create_file and not os.path_isfile(fp):
            os.touch(fp)

    def load(self, load_method=safe_load, encoding=None):
        return load_method(open(self.filepath, encoding=encoding or self.default_encoding))

    def dump(self, data, dump_method=safe_dump, encoding=None):
        return dump_method(data, open(self.filepath, 'w', encoding=encoding or self.default_encoding))
