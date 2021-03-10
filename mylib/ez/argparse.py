#!/usr/bin/env python3
from argparse import *

from . import AttrName

tn = the_name = AttrName()


class HelpCompactFormatter(HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            # noinspection PyProtectedMember
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(sorted(action.option_strings, reverse=True)) + ' ' + args_string


class DecoratingParser:
    def __init__(self, formatter_class=HelpCompactFormatter, **kwargs):
        self.parser_common_kwargs = dict(formatter_class=formatter_class, **kwargs)
        self.the_parser = ArgumentParser(**self.parser_common_kwargs)
        self.subparsers_kwargs: dict = {}
        self.subparsers = None
        self.config = {}

    def super_command(self, **kwargs):
        """factory decorator for the whole parser"""

        def deco(target):
            self.the_parser.set_defaults(__target_=target)
            for _name, _args, _kwargs in self.config[target]:
                getattr(self.the_parser, _name)(*_args, **_kwargs)
            return target

        return deco

    def sub_command(self, name=None, aliases=(), **kwargs):
        """factory decorator to add sub command, put this decorator on top"""
        if self.subparsers is None:
            self.subparsers = self.the_parser.add_subparsers(**self.subparsers_kwargs)
        parser_kwargs = dict(**self.parser_common_kwargs, **kwargs)

        def deco(target):
            sub_command = name or target.__name__
            sub_parser = self.subparsers.add_parser(name=sub_command, aliases=aliases, **parser_kwargs)
            sub_parser.set_defaults(__target__=target)
            for _name, _args, _kwargs in self.config[target]:
                getattr(sub_parser, _name)(*_args, **_kwargs)
            return target

        return deco

    def argument(self, *args, **kwargs):
        """factory decorator to add argument"""
        return self._deco_factory_add_sth('argument', *args, **kwargs)

    def argument_group(self, *args, **kwargs):
        return self._deco_factory_add_sth('argument_group', *args, **kwargs)

    def _deco_factory_add_sth(self, sth_name, *args, **kwargs):
        def deco(target):
            self.config.setdefault(target, []).insert(0, (f'add_{sth_name}', args, kwargs))
            return target

        return deco

    def __getattr__(self, item):
        return getattr(self.the_parser, item)
