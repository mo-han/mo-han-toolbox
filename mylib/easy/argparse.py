#!/usr/bin/env python3
import re
from argparse import *

from . import typing, SingletonMetaClass, AttrName

T = typing


class CompactHelpFormatterWithDefaults(ArgumentDefaultsHelpFormatter):
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


class UnknownArgumentsPlaceholder(metaclass=SingletonMetaClass):
    pass


class ArgumentParserRigger:
    def __init__(self, formatter_class=CompactHelpFormatterWithDefaults,
                 subcommands_title='sub-cmd', subcommands_desc=None, **kwargs):
        self.parser_common_kwargs = dict(formatter_class=formatter_class, **kwargs)
        self.root_parser = ArgumentParser(**self.parser_common_kwargs)
        self.subparsers_kwargs = dict(title=subcommands_title, description=subcommands_desc)
        self.subparsers = None
        self.arguments_config = {}
        self.target_call_config = {}
        self.namespace: T.Optional[Namespace] = None
        self.unknown_args: T.List[str] = []
        self.last_target = None
        self.option_names = ['-h', '--help']

    def get_arg(self, arg_dest: str, default=None):
        return self.namespace.__dict__.get(arg_dest, default)

    @property
    def unknown_placeholder(self):
        return UnknownArgumentsPlaceholder()

    @staticmethod
    def raw_object(x):
        return RawObject(x)

    @property
    def attr_name(self):
        return AttrName()

    @staticmethod
    def replace_underscore(repl: str = '.'):
        def rename(x: str):
            return x.replace('_', repl)

        return rename

    def find(self, name: str, default=None):
        try:
            return getattr(self.namespace, name)
        except AttributeError:
            return default

    def map_args_to_target_params(self, *args: str or RawObject or UnknownArgumentsPlaceholder,
                                  **kwargs: str or RawObject or UnknownArgumentsPlaceholder):
        """factory decorator to map arguments to the signature of decorated callable target"""

        def deco(target):
            self.target_call_config[target] = args, kwargs
            return target

        return deco

    def parse(self, *args, catch_unknown_args=False, **kwargs):
        parse = self.parse_known_args if catch_unknown_args else self.parse_args
        return parse(*args, **kwargs)

    def run_target(self):
        """call target"""
        try:
            self.last_target = target = self.namespace.__target__
        except AttributeError:
            self.last_target = None
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
        elif isinstance(x, UnknownArgumentsPlaceholder):
            return self.unknown_args
        else:
            return getattr(self.namespace, x)

    def super_command(self):
        """factory decorator for the whole parser"""

        def deco(target):
            self.root_parser.set_defaults(__target__=target)
            for _name, _args, _kwargs in self.arguments_config.get(target, []):
                getattr(self.root_parser, _name)(*_args, **_kwargs)
            return target

        return deco

    def sub_command(self, rename=None, aliases=(), **kwargs):
        """factory decorator to add sub command, put this decorator on top"""
        if self.subparsers is None:
            self.subparsers = self.root_parser.add_subparsers(**self.subparsers_kwargs)
        parser_kwargs = dict(**self.parser_common_kwargs, **kwargs)

        def deco(target):
            if not parser_kwargs.get('help') and target.__doc__:
                parser_kwargs['help'] = target.__doc__
            if not rename:
                sub_name = target.__name__
            elif isinstance(rename, str):
                sub_name = rename
            else:
                sub_name = rename(target.__name__)
            sub_parser = self.subparsers.add_parser(name=sub_name, aliases=aliases, **parser_kwargs)
            sub_parser.set_defaults(__target__=target)
            for _name, _args, _kwargs in self.arguments_config.get(target, []):
                getattr(sub_parser, _name)(*_args, **_kwargs)
            return target

        return deco

    def argument(self, *args, **kwargs):
        """factory decorator to add argument"""
        return self._deco_factory_add_sth('argument', *args, **kwargs)

    def argument_group(self, *args, **kwargs):
        return self._deco_factory_add_sth('argument_group', *args, **kwargs)

    @staticmethod
    def make_option_name_from_dest_name(dest_name):
        return re.sub(r'[\W_]+', '-', dest_name)

    @staticmethod
    def make_dest_name_from_option_name(option_name):
        return re.sub(r'\W+', '_', option_name)

    def option(self, short_name: str = None, long_name: str = None, **kwargs):
        opts = []
        if short_name:
            opts.append('-' + short_name)
        if long_name:
            opts.append('--' + long_name)
        self.option_names.extend(opts)
        return self.argument(*opts, **kwargs)

    def flag(self, short_name: str = None, long_name: str = None, *, action='store_true', **kwargs):
        """'store_true' option"""
        return self.option(short_name, long_name=long_name, action=action, **kwargs)

    def flag_reverse(self, short_name: str = None, long_name: str = None, **kwargs):
        """'store_false' option"""
        return self.flag(short_name, long_name=long_name, action='store_false', **kwargs)

    def _deco_factory_add_sth(self, sth_name, *args, **kwargs):
        def deco(target):
            self.arguments_config.setdefault(target, []).insert(0, (f'add_{sth_name}', args, kwargs))
            return target

        return deco

    def __getattr__(self, item):
        p = self.root_parser
        if item in ('parse_args', 'parse_intermixed_args'):
            def to_be_returned(*args, **kwargs):
                self.namespace = getattr(p, item)(*args, **kwargs)
                return self.namespace
        elif item in ('parse_known_args', 'parse_known_intermixed_args'):
            def to_be_returned(*args, **kwargs):
                self.namespace, self.unknown_args = getattr(p, item)(*args, **kwargs)
                return self.namespace, self.unknown_args
        else:
            to_be_returned = getattr(p, item)
        return to_be_returned

    arg = argument
    opt = option
    true = flag
    false = flag_reverse
    grp = argument_group
    root = super_command
    sub = sub_command
    map = map_args_to_target_params
    run = run_target
    ro = raw_object
    skip = unknown_placeholder
    an = attr_name
    dst2opt = make_option_name_from_dest_name
    opt2dst = make_dest_name_from_option_name
