#!/usr/bin/env python3
from ezpykit.allinone import ctx_ensure_module, logging

__logger__ = logging.get_logger(__name__)

with ctx_ensure_module('colorama'):
    import colorama

with ctx_ensure_module('termcolor'):
    from termcolor import *

colorama.init()

___ref = [cprint]


def styled(text, stylesheet=None):
    kwargs = {}
    ss = stylesheet
    if not ss:
        return colored(text)
    if isinstance(ss, str):
        ss = ss.split()
    ss = list(ss)

    on_colors = []
    for x in ss:
        if x.startswith('on'):
            on_colors.append(x)
            bg = x[2:].strip('-_')
            if bg in COLORS.keys():
                kwargs['on_color'] = bg
            else:
                __logger__.warning(f'ignore invalid background color: {bg}')

    attributes = []
    for x in ss:
        if x in ATTRIBUTES.keys() and x not in attributes:
            attributes.append(x)
    kwargs['attrs'] = attributes

    possible_colors = [e for e in ss if e not in attributes and e not in on_colors]
    for c in possible_colors:
        if c in COLORS.keys():
            kwargs['on_color'] = c
        else:
            __logger__.warning(f'ignore invalid color: {c}')

    return colored(text, **kwargs)
