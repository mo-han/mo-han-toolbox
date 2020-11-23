#!/usr/bin/env python3
# encoding=utf8

import inflection

from .tricks_base import *


def get_first_return(tasks: Iterable[dict], common_exception=Exception):
    """try through a sequence of calling, until anyone returns, then stop and return that value.

    Args:
        tasks: a sequence of task,
            which is a dict, consisting of a callable ``target`` (required),
            with optional items ``args``, ``kwargs``, ``exceptions``, see below,
            {'target': ``target``, 'args': ``args``, 'kwargs': ``kwargs``, 'exceptions': ``exceptions``}.
            every task is called like `target(*args, **kwargs)`, if


    during the calling sequence, if the target raise any error, it will be handled in two ways:
        if the error fit the given exception type, it will be ignored;
        else, it will be raised, which will stop the whole calling sequence.
    """
    for task in tasks:
        exception = task.get('exception', common_exception)
        args = task.get('args', ())
        kwargs = task.get('kwargs', {})
        try:
            return task['target'](*args, **kwargs)
        except exception:
            pass


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
    import dill
    dill.detect.trace(dill_detect_trace)
    import sqlitedict
    sqlitedict.dumps = dill.dumps
    sqlitedict.loads = dill.loads
    sqlitedict.PICKLE_PROTOCOL = dill.HIGHEST_PROTOCOL
    return sqlitedict


def is_picklable_with_dill_trace(obj, exact=False, safe=False, **kwds):
    import dill
    args = (obj,)
    kwargs = dict(exact=exact, safe=safe, **kwds)
    if dill.pickles(*args, **kwargs):
        return True
    else:
        dill.detect.trace(True)
        return dill.pickles(*args, **kwargs)
