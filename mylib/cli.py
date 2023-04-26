#!/usr/bin/env python3
# encoding=utf8
import argparse

from oldezpykit.stdlib.argparse import CompactHelpFormatterWithDefaults
from mylib.math import int_is_power_of_2


def arg_type_pow2(x):
    i = int(x)
    if int_is_power_of_2(i):
        return i
    else:
        raise argparse.ArgumentTypeError("'{}' is not power of 2".format(x))


def arg_type_range_factory(x_type, x_range_condition: str):
    def arg_type_range(x):
        x = x_type(x)
        if eval(x_range_condition):
            return x
        else:
            raise argparse.ArgumentTypeError("'{}' not in range {}".format(x, x_range_condition))

    return arg_type_range


def new_argument_parser(formatter_class=CompactHelpFormatterWithDefaults):
    return argparse.ArgumentParser(formatter_class=formatter_class)


def add_dry_run(parser: argparse.ArgumentParser):
    parser.add_argument('-D', '--dry-run', action='store_true')
