#!/usr/bin/env python3
# encoding=utf8
from .tricks import modify_and_import


def code_modify_pip2pi(x: str) -> str:
    x = x.replace("""
    def add_index_options(self):
""", """
    def add_index_options(self):
        self.add_option(
            '-A', '--absolute-symlink', dest='absolute_symlink',
            default=False, action='store_true',
            help='Use absolute path symlink (default is relative path).'
        )
""")
    x = x.replace("""
        try_symlink(option, symlink_source, symlink_target)
""", """
        if option.absolute_symlink:
            symlink_source = os.path.abspath(os.path.join("../../", pkg_basename))
        else:
            symlink_source = os.path.join("../../", pkg_basename)
""")
    return x


libpip2pi_commands_x = modify_and_import('libpip2pi.commands', code_modify_pip2pi)
