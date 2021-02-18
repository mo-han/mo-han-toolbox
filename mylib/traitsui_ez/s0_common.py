#!/usr/bin/env python3
# encoding=utf8
import traits.observation.api as ob_api
import traits.observation.events as ob_evt
import traits.observation.expression as ob_exp
from pyface.api import *
from traits.api import *
from traitsui.api import *
from traitsui.key_bindings import *
from varname import nameof

from ..ez import *

TraitChangeEvent = ob_evt.TraitChangeEvent


def __unused_import_keeper():
    return ImageResource, ob_api, ob_exp


class UsefulHandler(Handler):
    def __hdlr_do_nothing__(self, *args):
        pass

    @staticmethod
    def __hdlr_close_view__(info: UIInfo):
        if not info.initialized:
            return
        info.ui.dispose()

    @staticmethod
    def __hdlr_quit__(*args):
        sys.exit()

    def __hdlr_close_view_and_quit__(self, info: UIInfo):
        self.__hdlr_close_view__(info)
        self.__hdlr_quit__()


KB_ESC_NOTHING = KeyBinding(binding1='Esc', method_name=UsefulHandler.__hdlr_do_nothing__.__name__)
KB_ESC_CLOSE = KeyBinding(binding1='Esc', method_name=UsefulHandler.__hdlr_close_view__.__name__)
KB_ESC_QUIT = KeyBinding(binding1='Esc', method_name=UsefulHandler.__hdlr_quit__.__name__)


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


def var_name_path(*obj):
    return nameof(*obj, caller=2, full=True)


def object_trait_name(trait_name):
    return f'object.{trait_name}'


tn = the_name = TraitName()
tl = trait_with_label
ti = trait_with_id
vn = var_name
vp = var_name_path
ot = object_trait_name
