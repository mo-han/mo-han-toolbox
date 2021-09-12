#!/usr/bin/env python3
from mylib.easy.fstk import *
from mylib.ext import tricks


def __ref():
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


def does_file_mime_has(file, mime_keyword):
    from filetype import filetype
    guess = filetype.guess(file)
    return guess and mime_keyword in guess.mime
