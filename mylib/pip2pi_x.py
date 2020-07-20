#!/usr/bin/env python3
# encoding=utf8
from .tricks import modify_and_import


def code_modify_pip2pi(x: str) -> str:
    x = x.replace("""
        self.add_option(
            '-S', '--no-symlink', dest="use_symlink", action="store_false")
""", """
        self.add_option(
            '-A', '--absolute-symlink', dest='absolute_symlink',
            default=False, action='store_true',
            help='Use absolute path symlink (default is relative path).'
        )
        self.add_option(
            '-S', '--no-symlink', dest="use_symlink", action="store_false")
""")
    x = x.replace("""
        symlink_source = os.path.join("../../", pkg_basename)
""", """
        if option.absolute_symlink:
            symlink_source = os.path.abspath(os.path.join("../../", pkg_basename))
        else:
            symlink_source = os.path.join("../../", pkg_basename)
""")
    return x


libpip2pi_commands_x = modify_and_import('libpip2pi.commands', code_modify_pip2pi)
