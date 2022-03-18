#!/usr/bin/env python3
import contextlib
import os
import os as _os

from ezpykit.builtin import ezlist
from ezpykit.metautil import T

get_dirname = _os.path.dirname
get_basename = _os.path.basename
join_path = _os.path.join
split_path = _os.path.split
split_ext = _os.path.splitext
tilde_path = _os.path.expanduser
envar_path = _os.path.expandvars
path_exists = _os.path.exists
path_isfile = _os.path.isfile
path_isdir = _os.path.isdir


class EnVarKit:
    upper_case = True
    path_sep = None

    @classmethod
    def valid_key(cls, k):
        return str(k).upper() if cls.upper_case else str(k)

    @classmethod
    def set(cls, *args, **kwargs):
        for data in [*args, kwargs]:
            for k, v in data.items():
                _os.environ[cls.valid_key(k)] = str(v)

    @classmethod
    def save(cls, *args, **kwargs):
        raise NotImplementedError(_os.name)

    @classmethod
    def get_saved_path_list(cls, *args, **kwargs):
        raise NotImplementedError(_os.name)

    @classmethod
    def save_path_replace(cls, paths: T.Union[str, T.Iterable[str]]):
        name = 'PATH'
        if isinstance(paths, str):
            value = paths
        else:
            value = cls.path_sep.join(paths)
        cls.save({name: value})

    @classmethod
    def save_path(cls, insert: T.Iterable[str] = None, remove: T.Iterable[str] = None, append: T.Iterable[str] = None):
        name = 'PATH'
        paths = cls.get_saved_path_list()
        if insert:
            for i in insert:
                ezlist.remove_all(paths, str(i))
            paths = list(insert) + paths
        if remove:
            for r in remove:
                ezlist.remove_all(paths, str(r))
        if append:
            for a in append:
                ezlist.remove_all(paths, str(a))
            paths = paths + list(append)
        cls.save({name: cls.path_sep.join(paths)})


@contextlib.contextmanager
def ctx_pushd(dst, ensure_dst: bool = False):
    if dst == '':
        yield
        return
    if ensure_dst:
        cd = ensure_chdir
    else:
        cd = os.chdir
    prev = os.getcwd()
    error = None
    try:
        cd(dst)
        yield
    except Exception as e:
        error = e
    finally:
        cd(prev)
        if error:
            raise error


def ensure_chdir(dest):
    if not os.path.isdir(dest):
        os.makedirs(dest, exist_ok=True)
    os.chdir(dest)
