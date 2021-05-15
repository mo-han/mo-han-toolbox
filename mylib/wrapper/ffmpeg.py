#!/usr/bin/env python3
from mylib.easy import *


class CLIArgs(CLIArgumentsList):
    merge_option_nargs = False

    @staticmethod
    def _spec_convert_keyword_to_option_name(keyword):
        return '-' + keyword.replace('___', '-').replace('__', ':')
