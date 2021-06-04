#!/usr/bin/env python3
# encoding=utf8
from enable.savage.trait_defs.ui.svg_button import SVGButton
from pyface.api import *
from traitsui.api import *
from traitsui.key_bindings import *

from .i1_traits import *


def __unused_import_keeper():
    return ImageResource, TraitType, SVGButton


class SimpleHandler(Handler):
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


KB_ESC_NOTHING = KeyBinding(binding1='Esc', method_name=SimpleHandler.__hdlr_do_nothing__.__name__)
KB_ESC_CLOSE = KeyBinding(binding1='Esc', method_name=SimpleHandler.__hdlr_close_view__.__name__)
KB_ESC_QUIT = KeyBinding(binding1='Esc', method_name=SimpleHandler.__hdlr_quit__.__name__)
