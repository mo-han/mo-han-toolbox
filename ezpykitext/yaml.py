#!/usr/bin/env python3
from ezpykit.stdlib.io import IOKit

try:
    import yaml
except ModuleNotFoundError:
    import os

    os.system('pip install pyyaml')
    import yaml

DEFAULT_ENCODING = 'UTF-8-SIG'


class EzYAML:
    filename = None
    documents = None
    encoding = DEFAULT_ENCODING

    def set_file(self, fp, encoding=DEFAULT_ENCODING):
        self.filename = fp
        self.encoding = encoding
        return self

    def set_doc(self, documents):
        self.documents = documents
        return self

    def load(self, stream=None, as_list=True):
        stream = stream or IOKit.read_exit(open(self.filename, encoding=self.encoding))
        self.documents = yaml.safe_load_all(stream)
        if as_list:
            self.documents = list(self.documents)
        return self

    def dump(self, **kwargs):
        return yaml.safe_dump_all(self.documents, **kwargs)

    def save(self, encoding=None, allow_unicode=True, **kwargs):
        self.save_as(self.filename, encoding=encoding, allow_unicode=allow_unicode, **kwargs)
        return self

    def save_as(self, fp, encoding=None, allow_unicode=True, **kwargs):
        with open(fp, 'wb') as f:
            yaml.safe_dump_all(
                self.documents,
                f,
                encoding=encoding or self.encoding,
                allow_unicode=allow_unicode,
                **kwargs
            )
        return self
