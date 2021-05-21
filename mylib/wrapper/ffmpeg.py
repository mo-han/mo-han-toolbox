#!/usr/bin/env python3
from mylib.easy import *
from mylib.easy import logging


class CLIArgs(CLIArgumentsList):
    merge_option_nargs = False

    @staticmethod
    def _spec_convert_keyword_to_option_name(keyword):
        return '-' + keyword.replace('___', '-').replace('__', ':')


class Error(Exception):
    def __init__(self, exit_code: int, stderr_content: str):
        self.exit_code = exit_code
        self.stderr_lines = stderr_content.splitlines()
        self.cause = None, None, None
        for es in self.stderr_lines:
            if es.startswith('Unknown encoder'):
                self.cause = 'encoder', 'unknown', es[17:-1]
            elif 'Error loading plugins' in es:
                self.cause = 'plugin', 'load', None


class FFmpeg:
    ...
