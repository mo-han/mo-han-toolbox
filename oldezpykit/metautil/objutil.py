#!/usr/bin/env python3
from functools import lru_cache
from types import MethodType

from oldezpykit.metautil import typing as T


def hashable_args_kwargs_tuple(*args, **kwargs):
    return tuple(args), tuple(kwargs.items())


class VoidDuck:
    """a void, versatile, useless and quiet duck, call in any way, return nothing, raise nothing"""

    def __init__(self, *args, **kwargs):
        pass

    def _get_self(self, *args, **kwargs):
        return self

    __call__ = __getattr__ = __getitem__ = __setattr__ = __setitem__ = _get_self

    def __bool__(self):
        return False


class DummyObject:
    def __init__(self, _ref_obj=None, **settings):
        self._settings = settings
        self._ref_obj = _ref_obj

    def _get_sth(self, name):
        return self._settings[name]

    def __getattr__(self, item):
        if item in self._settings:
            def f(*args, **kwargs):
                return self._get_sth(item)

            f.__name__ = item
            self.__dict__[item] = f
            return f
        elif self._ref_obj:
            return getattr(self._ref_obj, item)
        else:
            raise AttributeError(item)


class PropertiesWrapper:
    attr_name = '__user_properties__'
    cached_instances = {}

    def __init__(self, obj):
        d = getattr(obj, self.attr_name, None)
        if not isinstance(d, dict):
            setattr(obj, self.attr_name, {})
        else:
            self._dict = {}
        self._obj = obj

    @classmethod
    @lru_cache()
    def new(cls, obj) -> T.Union['PropertiesWrapper', dict]:
        instances = cls.cached_instances
        if obj in instances:
            return instances[obj]
        else:
            new = cls(obj)
            instances[obj] = new
            return new

    @property
    def obj(self):
        return self._obj

    @property
    def prop(self):
        return getattr(self._obj, self.attr_name) if self._obj_has_dict else self._dict

    def __getattr__(self, item):
        return getattr(self.prop, item)

    def __getitem__(self, item):
        return self.prop[item]

    def __setitem__(self, key, value):
        self.prop[key] = value


class AttachMethodsToObject:
    class Util:
        @classmethod
        def deco_enable_method(cls, f):
            PropertiesWrapper.new(f)['enabled'] = True
            return f

    @classmethod
    def attach(cls: T.T, obj: T.VT) -> T.Union[T.VT, T.T]:
        cls: AttachMethodsToObject
        for m in cls.__dict__.values():
            if callable(m) and PropertiesWrapper.new(m).get('enabled'):
                setattr(obj, m.__name__, MethodType(m, obj))
        return obj
