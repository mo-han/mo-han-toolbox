#!/usr/bin/env python3
# encoding=utf8
from pyface.api import *
from traits.api import *
from traitsui.api import *
from traitsui.key_bindings import *
from varname import nameof

from ..ez import *


def __unused_import_keeper():
    return ImageResource


class UsefulHandler(Handler):
    def __hdl_do_nothing__(self, *args):
        pass

    @staticmethod
    def __hdl_close_view__(info: UIInfo):
        if not info.initialized:
            return
        info.ui.dispose()

    @staticmethod
    def __hdl_quit__(*args):
        sys.exit()

    def __hdl_close_view_and_quit__(self, info: UIInfo):
        self.__hdl_close_view__(info)
        self.__hdl_quit__()


KB_ESC_NOTHING = KeyBinding(binding1='Esc', method_name=UsefulHandler.__hdl_do_nothing__.__name__)
KB_ESC_CLOSE = KeyBinding(binding1='Esc', method_name=UsefulHandler.__hdl_close_view__.__name__)
KB_ESC_QUIT = KeyBinding(binding1='Esc', method_name=UsefulHandler.__hdl_quit__.__name__)


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


class TraitName(AttrToStr):
    def __setattr__(self, key, value):
        super(TraitName, self).__setattr__(key, value)
        trait_with_id(value, key)


def var_name(*obj):
    return nameof(*obj, caller=2)


def var_path_name(*obj):
    return nameof(*obj, caller=2, full=True)


def object_path(trait_name):
    return f'object.{trait_name}'


tn = the_name = TraitName()
tl = trait_with_label
ti = trait_with_id
vn = var_name
vp = var_path_name
op = object_path
