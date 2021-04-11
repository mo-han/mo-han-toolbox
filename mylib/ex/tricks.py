#!/usr/bin/env python3
# encoding=utf8
import dill
import inflection
import sqlitedict

from .tricks_lite import *

assert USELESS_PLACEHOLDER_FOR_MODULE_TRICKS_LITE


class AttributeInflection:
    def __getattribute__(self, item):
        if item == '__dict__':
            return object.__getattribute__(self, item)
        item_camel = inflection.camelize(item, False)
        underscore = inflection.underscore
        if item in self.__dict__:
            return self.__dict__[item]
        elif item_camel in self.__dict__ or item in [underscore(k) for k in self.__dict__]:
            return self.__dict__[item_camel]
        else:
            return object.__getattribute__(self, item)


def module_sqlitedict_with_dill(*, dill_detect_trace=False):
    dill.detect.trace(dill_detect_trace)
    sqlitedict.dumps = dill.dumps
    sqlitedict.loads = dill.loads
    sqlitedict.PICKLE_PROTOCOL = dill.HIGHEST_PROTOCOL
    return sqlitedict


def is_picklable_with_dill_trace(obj, exact=False, safe=False, **kwds):
    args = (obj,)
    kwargs = dict(exact=exact, safe=safe, **kwds)
    if dill.pickles(*args, **kwargs):
        return True
    else:
        dill.detect.trace(True)
        r = dill.pickles(*args, **kwargs)
        dill.detect.trace(False)
        return r