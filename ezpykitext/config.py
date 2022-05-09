#!/usr/bin/env python3
from ezpykit.wip.config import *
from ezpykit.allinone import *
import codecs


def is_utf8_encoding(x):
    u8 = codecs.lookup('utf-8')
    return codecs.lookup(x) == u8


class FileConfigMixin:
    filepath = None
    encoding = 'utf8'

    def _dump_data_to_bytes(self):
        raise NotImplementedError(self._dump_data_to_bytes.__name__)

    def save_data(self):
        fp = self.filepath
        s = self._dump_data_to_bytes()
        if not fp:
            return s
        io.IOKit.write_exit(open(fp, 'wb'), s)

    def exists(self):
        fp = self.filepath
        if not fp:
            return False
        return os.path_isfile(fp)


class YAMLConfig(DictConfig, FileConfigMixin):
    def __init__(self, filepath=None, stream: str = None):
        import yaml
        s = '{}'
        if filepath:
            self.filepath = filepath
            if self.exists():
                with open(filepath, encoding=self.encoding) as f:
                    s = f.read()
        if stream:
            s = stream
        self.set_data(yaml.safe_load(s))

    def _dump_data_to_bytes(self):
        import yaml
        return yaml.safe_dump(self.data, encoding=self.encoding)


class JSONConfigSource(DictConfig, FileConfigMixin):
    def __init__(self, filepath=None, string=None):
        import json
        if filepath:
            self.filepath = filepath
            if self.exists():
                self.set_data(json.load(filepath, encodings=self.encoding))
        elif string:
            self.set_data(json.loads(string))
        else:
            raise ValueError('neither filepath nor string')

    def _dump_data_to_bytes(self):
        import json
        return json.dumps(self.data, indent=4, ensure_ascii=not is_utf8_encoding(self.encoding)).encode(self.encoding)


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
