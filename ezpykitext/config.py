#!/usr/bin/env python3
from ezpykit.config import *


class YAMLConfig(DictConfig):
    encoding = 'utf8'

    def __init__(self, filepath=None, document: str = None):
        import yaml

        if filepath:
            with open(filepath, encoding=self.encoding) as f:
                s = f.read()
        elif document:
            s = document
        else:
            raise ValueError('neither filepath nor document')
        self.set_data(yaml.safe_load(s))


class JSONConfigSource(DictConfig):
    encoding = 'utf8'

    def __init__(self, filepath=None, string=None):
        import json

        if filepath:
            self.set_data(json.load(filepath, encodings=self.encoding))
        elif string:
            self.set_data(json.loads(string))
        else:
            raise ValueError('neither filepath nor string')


class UnionConfig:
    def __init__(self, *config: ConfigABC):
        self.config_sequence = config

    def __contains__(self, item):
        for config in self.config_sequence:
            if item in config:
                return True
        return False

    def __getitem__(self, item):
        for c in self.config_sequence:
            if item in c:
                return c[item]
        raise KeyError(item)
