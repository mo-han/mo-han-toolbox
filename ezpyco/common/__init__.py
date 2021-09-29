#!/usr/bin/env python3
import glob as glob
import itertools as itertools
import pathlib as pathlib
import queue as queue
import re as re
import subprocess as subprocess
import sys as sys
import time as time

from ezpyco.stdlib import typing

T = typing
sleep = time.sleep


def __avoid_pycharm_optimize_imports():
    return queue, re, sys, subprocess, time, pathlib, glob, itertools
