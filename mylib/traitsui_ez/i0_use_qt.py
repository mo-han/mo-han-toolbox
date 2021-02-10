#!/usr/bin/env python3
# encoding=utf8
from traits.etsconfig.api import ETSConfig

TRAITS_TOOLKIT = ETSConfig.toolkit = 'qt4'


def make_item_style_sheet(
        *,
        font_px: int = None,
        font_bold: bool = False,
        font_italic: bool = False,
        font_family: str = None,
        color: str = None,
        color_bg: str = None
):
    font_l = [e for e in (
        # order matters
        'italic' if font_italic else '',
        'bold' if font_bold else '',
        f'{font_px}px' if font_px else '',
        font_family
    ) if e]
    sec_l = [f'font: {" ".join(font_l)}']
    sec_l.append(f'color: {color}') if color else ...
    sec_l.append(f'background: {color_bg}') if color_bg else ...
    ss = '; '.join(sec_l)
    print(ss)
    return ss
