#!/usr/bin/env python3
from ezpykit.allinone import *
from ezpykitext import os, webclient

apr = argparse.ArgumentParserWrapper()


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
