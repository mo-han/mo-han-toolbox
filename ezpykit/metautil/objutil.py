#!/usr/bin/env python3
from functools import lru_cache
from types import MethodType

from ezpykit.metautil import typing as T


class ManagePropertiesAttribute:
    attr_name = '__user_properties__'
    instances = {}

    def __init__(self, obj):
        has_dict = self._obj_has_dict = hasattr(obj, '__dict__')
        if has_dict:
            d = getattr(obj, self.attr_name, None)
            if not isinstance(d, dict):
                setattr(obj, self.attr_name, {})
            else:
                self._dict = {}
            self._obj = obj

    @classmethod
    @lru_cache()
    def get_instance(cls, obj):
        instances = cls.instances
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


class AttachInstanceMethods:
    class Util:
        @classmethod
        def deco_enable_method(cls, func):
            ManagePropertiesAttribute.get_instance(func)['enabled'] = True
            return func

    @classmethod
    def attach(cls: T.T, instance: T.VT) -> T.Union[T.VT, T.T]:
        for m in cls.__dict__.values():
            if callable(m) and ManagePropertiesAttribute.get_instance(m).get('enabled'):
                setattr(instance, m.__name__, MethodType(m, instance))
        return instance
