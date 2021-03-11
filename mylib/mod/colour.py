#!/usr/bin/env python3
from ..ez import *
import colour


class Color(colour.Color):
    HEX_PATTERN_3 = r'[0-9a-fA-F]{3}'
    HEX_PATTERN_6 = r'[0-9a-fA-F]{6}'
    HEX_PATTERN_GROUP = rf'({HEX_PATTERN_3}|{HEX_PATTERN_6})'

    def as_hex(self, x: str):
        x = str_remove_prefix(x, '#')
        if re.match(self.HEX_PATTERN_3, x):
            self.set_hex(f'#{x}')
        elif re.match(self.HEX_PATTERN_6, x):
            self.set_hex_l(f'#{x}')
        else:
            raise ValueError(x)
        return self

    def as_rgb(self, r: int, g: int, b: int):
        rgb = (r, g, b)
        hex_s = ''.join([f'{i:02x}' for i in rgb])
        return self.as_hex(hex_s)

    def __getattr__(self, item):
        match = re.match(self.as_hex.__name__ + '_' + self.HEX_PATTERN_GROUP, item)
        if match:
            hex_s = match.group(1)
            return self.as_hex(hex_s)
        match = re.match(self.as_rgb.__name__ + '_' + r'(\d{1,3})_(\d{1,3})_(\d{1,3})', item)
        if match:
            r, g, b = [int(s) for s in match.groups()]
            return self.as_rgb(r, g, b)
        return super(Color, self).__getattr__(item)
