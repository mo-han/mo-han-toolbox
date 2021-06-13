#!/usr/bin/env python3
from filetype import filetype

from mylib.easy.fstk import *
from . import tricks


def __refer_sth():
    return POTENTIAL_INVALID_CHARS_MAP


def read_sqlite_dict_file(filepath, *, with_dill=False, **kwargs):
    if with_dill:
        sqlitedict = tricks.module_sqlitedict_with_dill(dill_detect_trace=True)
    else:
        import sqlitedict
    with sqlitedict.SqliteDict(filepath, **kwargs) as sd:
        return dict(sd)


def write_sqlite_dict_file(filepath, data, *, with_dill=False, dill_detect_trace=False, update_only=False, **kwargs):
    if with_dill:
        sqlitedict = tricks.module_sqlitedict_with_dill(dill_detect_trace=dill_detect_trace)
    else:
        import sqlitedict
    with sqlitedict.SqliteDict(filepath, **kwargs) as sd:
        if not update_only:
            sd.clear()
        sd.update(data)
        sd.commit()


def file_mime_has(file, what):
    guess = filetype.guess(file)
    return guess and what in guess.mime