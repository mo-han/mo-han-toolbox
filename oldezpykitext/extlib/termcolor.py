#!/usr/bin/env python3
from oldezpykit.allinone import ctx_ensure_module, logging

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
            on_color = f'on_{bg}'
            if on_color in HIGHLIGHTS.keys():
                kwargs['on_color'] = on_color
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
            kwargs['color'] = c
        else:
            __logger__.warning(f'ignore invalid color: {c}')

    try:
        return colored(text, **kwargs)
    except Exception:
        __logger__.error(f'{text}, {kwargs}')
        raise
