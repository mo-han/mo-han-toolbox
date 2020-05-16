#!/usr/bin/env python3
# encoding=utf8


def is_power_of_2_int(x: int):
    if x > 1:
        return x & (x - 1) == 0
    elif x == 1:
        return True
    else:
        return False


class Pow2(int):
    def __new__(cls, x):
        new = super(Pow2, cls).__new__(cls, x)
        print(new)
        if is_power_of_2_int(new):
            return new
        else:
            raise ValueError("invalid literal for {}(): '{}'".format(cls.__name__, x))
