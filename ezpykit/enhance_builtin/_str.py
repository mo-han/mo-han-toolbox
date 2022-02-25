#!/usr/bin/env python3
from ezpykit.base import decofac_add_method_to_class


class EzStr(str):
    ...


if not hasattr(EzStr, 'removeprefix'):
    @decofac_add_method_to_class(EzStr, 'removeprefix')
    def str_remove_prefix(s: str, prefix: str):
        return s[len(prefix):] if s.startswith(prefix) else s

if not hasattr(EzStr, 'removesuffix'):
    @decofac_add_method_to_class(EzStr, 'removesuffix')
    def str_remove_suffix(s: str, suffix: str):
        return s[len(suffix):] if s.endswith(suffix) else s
