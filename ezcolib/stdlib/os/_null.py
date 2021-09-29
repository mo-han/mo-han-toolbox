#!/usr/bin/env python3
import os as _os

ez_dirname = _os.path.dirname
ez_basename = _os.path.basename
ez_join_path = _os.path.join
ez_tilde_path = _os.path.expanduser
ez_envar_path = _os.path.expandvars


class EzEnvVar:
    @staticmethod
    def set(*args, **kwargs):
        for data in [*args, kwargs]:
            for k, v in data.items():
                _os.environ[k] = v

    @staticmethod
    def save(*args, **kwargs):
        raise NotImplementedError(_os.name)