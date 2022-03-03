#!/usr/bin/env python3
import os as _os

path = _os.path
get_dirname = path.dirname
get_basename = path.basename
join_path = path.join
split_path = path.split
split_ext = path.splitext
tilde_path = path.expanduser
envar_path = path.expandvars
path_exists = path.exists
path_isfile = path.isfile
path_isdir = path.isdir


class EnVarKit:
    @staticmethod
    def set(*args, **kwargs):
        for data in [*args, kwargs]:
            for k, v in data.items():
                _os.environ[str(k)] = str(v)

    @staticmethod
    def save(*args, **kwargs):
        raise NotImplementedError(_os.name)
