#!/usr/bin/env python3
class ConfigSourceTypeEnum:
    yaml = 'yaml'


class YAMLFileLoader:
    def __init__(self, fp, encoding='utf8', **kwargs):
        import yaml
        x = yaml.safe_load(open(fp, encoding=encoding, **kwargs))
        if isinstance(x, dict):
            self.dict = x
        raise ValueError(f'the document is not a dict: {fp}')


class ConfigDict(dict):
    _loader_map = {ConfigSourceTypeEnum.yaml: YAMLFileLoader}
    src_type = ConfigSourceTypeEnum.yaml
    _current_node = None

    @property
    def current_node(self):
        if self._current_node is None:
            return self
