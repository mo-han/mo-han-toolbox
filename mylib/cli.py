#!/usr/bin/env python3
# encoding=utf8


class BoxDrawer:
    def __init__(self):
        self.chars = '─│'

    def vl(self, length=32):
        print(self.chars[0]*32)