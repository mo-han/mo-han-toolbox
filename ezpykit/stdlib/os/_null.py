#!/usr/bin/env python3
import os as _os

get_dirname = _os.path.dirname
get_basename = _os.path.basename
join_path = _os.path.join
tilde_path = _os.path.expanduser
envar_path = _os.path.expandvars


class EnvVar:
    @staticmethod
    def set(*args, **kwargs):
        for data in [*args, kwargs]:
            for k, v in data.items():
                _os.environ[k] = v

    @staticmethod
    def save(*args, **kwargs):
        raise NotImplementedError(_os.name)