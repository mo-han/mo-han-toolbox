#!/usr/bin/env python3
# encoding=utf8
from dearpygui.core import add_additional_font


def add_additional_font_uni(file='mylib/unifont-13.0.04.ttf', size=13):
    # https://github.com/hoffstadt/DearPyGui/issues/209#issuecomment-691930697
    add_additional_font(file, size,
                        custom_glyph_ranges=(
                            # the more ranges, the slower -> BAD METHOD!
                            (0x3400, 0x4dbf),  # CJK Unified Ideographs Extension A
                            (0x4E00, 0x9FFF),  # CJK Unified Ideographs (Chinese chars, Han unification)
                            (0x3040, 0x30ff),  # Japanese (Hiragana & Katakana)
                            (0xac00, 0xd7a3), (0x1100, 0x11ff), (0x3131, 0x318e), (0xffa1, 0xffdc),  # Korean
                            (0x0e00, 0x0e7f),  # Thai
                            (0x370, 0x377),  # Greek and Coptic
                            (0x400, 0x4ff),  # Cyrillic
                            (0x530, 0x58f),  # Armenian
                            (0x10a0, 0x10ff),  # Georgian
                        ))
