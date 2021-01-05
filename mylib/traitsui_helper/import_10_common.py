#!/usr/bin/env python3
# encoding=utf8
from traits.api import *
from traitsui.api import *
from traitsui.key_bindings import *

from mylib.ez import *

assert Trait


class SimpleHandler(Handler):
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


KB_ESC_NOTHING = KeyBinding(binding1='Esc', method_name=SimpleHandler.__hdl_do_nothing__.__name__)
KB_ESC_CLOSE = KeyBinding(binding1='Esc', method_name=SimpleHandler.__hdl_close_view__.__name__)
KB_ESC_QUIT = KeyBinding(binding1='Esc', method_name=SimpleHandler.__hdl_quit__.__name__)
