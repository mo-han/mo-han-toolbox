#!/usr/bin/env python3
# encoding=utf8
from traits.api import HasTraits
from varname import nameof

from mylib.easy import *


def trait_extra_attr_name(attr_name: str):
    return f'__extra_attr_{attr_name}__'


def trait_with_attr(traits_obj: HasTraits, name: str, value=...):
    if value is ...:
        return getattr(traits_obj, trait_extra_attr_name(name))
    else:
        setattr(traits_obj, trait_extra_attr_name(name), value)


def trait_with_label(traits_obj: HasTraits, label=...):
    attr_name = 'label'
    return trait_with_attr(traits_obj, attr_name, label)


def trait_with_id(traits_obj: HasTraits, id_=...):
    attr_name = 'id'
    return trait_with_attr(traits_obj, attr_name, id_)


class TraitName(AttrName):
    def __setattr__(self, key, value):
        super(TraitName, self).__setattr__(key, value)
        trait_with_id(value, key)


def var_name(*obj):
    return nameof(*obj, caller=2)


def var_name_path(*obj):
    return nameof(*obj, caller=2, full=True)


def object_trait_name(trait_name):
    return f'object.{trait_name}'


an = AttrName()
tn = TraitName()
tl = trait_with_label
ti = trait_with_id
vn = var_name
vp = var_name_path
ot = object_trait_name
