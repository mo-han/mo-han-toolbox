#!/usr/bin/env python3
if hasattr(str, 'removeprefix'):
    str_remove_prefix = str.removeprefix
else:
    def str_remove_prefix(s: str, prefix: str):
        return s[len(prefix):] if s.startswith(prefix) else s

if hasattr(str, 'removesuffix'):
    str_remove_suffix = str.removesuffix
else:
    def str_remove_suffix(s: str, suffix: str):
        return s[len(suffix):] if s.endswith(suffix) else s
