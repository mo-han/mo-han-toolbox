#!/usr/bin/env python3
from argparse import *

from . import typing, SingletonMetaClass

T = typing


class HelpCompactFormatter(HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            # noinspection PyProtectedMember
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(sorted(action.option_strings, reverse=True)) + ' ' + args_string


class RawObject:
    def __init__(self, obj):
        self.value = obj


class UnknownArguments(metaclass=SingletonMetaClass):
    pass


class ArgumentParserRigger:
    def __init__(self, formatter_class=HelpCompactFormatter, **kwargs):
        self.parser_common_kwargs = dict(formatter_class=formatter_class, **kwargs)
        self.the_parser = ArgumentParser(**self.parser_common_kwargs)
        self.subparsers_kwargs: dict = {}
        self.subparsers = None
        self.arguments_config = {}
        self.target_call_config = {}
        self.namespace: T.Optional[Namespace] = None
        self.unknown: T.List[str] = []

    @staticmethod
    def namer_factory_replace_underscore(repl: str = '.'):
        def namer(x: str):
            return x.replace('_', repl)

    def map_target_signature(self, *args: str or RawObject or UnknownArguments,
                             **kwargs: str or RawObject or UnknownArguments):
        """factory decorator to map arguments to the signature of decorated callable target"""

        def deco(target):
            self.target_call_config[target] = args, kwargs
            return target

        return deco

    def run_target(self):
        """call target"""
        try:
            target = self.namespace.__target__
        except AttributeError:
            return
        if target in self.target_call_config:
            t_args, t_kwargs = self.target_call_config[target]
            args = [self.restore_mapped_argument(a) for a in t_args]
            kwargs = {k: self.restore_mapped_argument(v) for k, v in t_kwargs.items()}
            return target(*args, **kwargs)
        else:
            return target()

    def restore_mapped_argument(self, x):
        if isinstance(x, RawObject):
            return x.value
        elif isinstance(x, UnknownArguments):
            return self.unknown
        else:
            return getattr(self.namespace, x)

    def super_command(self, **kwargs):
        """factory decorator for the whole parser"""

        def deco(target):
            self.the_parser.set_defaults(__target__=target)
            for _name, _args, _kwargs in self.arguments_config[target]:
                getattr(self.the_parser, _name)(*_args, **_kwargs)
            return target

        return deco

    def sub_command(self, namer=None, aliases=(), **kwargs):
        """factory decorator to add sub command, put this decorator on top"""
        if self.subparsers is None:
            self.subparsers = self.the_parser.add_subparsers(**self.subparsers_kwargs)
        parser_kwargs = dict(**self.parser_common_kwargs, **kwargs)

        def deco(target):
            if not namer:
                sub_command = target.__name__
            elif isinstance(namer, str):
                sub_command = namer
            else:
                sub_command = namer(target.__name__)
            sub_parser = self.subparsers.add_parser(name=sub_command, aliases=aliases, **parser_kwargs)
            sub_parser.set_defaults(__target__=target)
            for _name, _args, _kwargs in self.arguments_config[target]:
                getattr(sub_parser, _name)(*_args, **_kwargs)
            return target

        return deco

    def argument(self, *args, **kwargs):
        """factory decorator to add argument"""
        return self._deco_factory_add_sth('argument', *args, **kwargs)

    def argument_group(self, *args, **kwargs):
        return self._deco_factory_add_sth('argument_group', *args, **kwargs)

    def flag(self, short_flag: str, long_flag: str = None, **kwargs):
        """'store_true' option"""
        flags = ['-' + short_flag.strip('-')]
        if long_flag:
            flags.append('--' + long_flag.strip('-'))
        return self.argument(*flags, action='store_true', **kwargs)

    def flag_reverse(self, short_flag: str, long_flag: str = None, **kwargs):
        """'store_false' option"""
        flags = ['-' + short_flag.strip('-')]
        if long_flag:
            flags.append('--' + long_flag.strip('-'))
        return self.argument(*flags, action='store_false', **kwargs)

    def _deco_factory_add_sth(self, sth_name, *args, **kwargs):
        def deco(target):
            self.arguments_config.setdefault(target, []).insert(0, (f'add_{sth_name}', args, kwargs))
            return target

        return deco

    def __getattr__(self, item):
        p = self.the_parser
        if item == 'parse_args' or item == 'parse_intermixed_args':
            def to_be_returned(*args, **kwargs):
                self.namespace = getattr(p, item)(*args, **kwargs)
                return self.namespace
        elif item == 'parse_known_args' or item == 'parse_known_intermixed_args':
            def to_be_returned(*args, **kwargs):
                self.namespace, self.unknown = getattr(p, item)(*args, **kwargs)
                return self.namespace, self.unknown
        else:
            to_be_returned = getattr(p, item)
        return to_be_returned

    arg = argument
    grp = argument_group
    root = super_command
    sub = sub_command
    true = flag
    false = flag_reverse
    map = map_target_signature
    run = run_target
