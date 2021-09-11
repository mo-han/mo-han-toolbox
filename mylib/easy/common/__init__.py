#!/usr/bin/env python3
# !/usr/bin/env python3
import glob as glob
import itertools as itertools
import os as os
import pathlib as pathlib
import queue as queue
import re as re
import subprocess as subprocess
import sys as sys
import time as time

from mylib.easy.stdlibs import typing as typing

T = typing
sleep = time.sleep


def __refer_sth():
    return queue, re, sys, subprocess, time, pathlib, glob, itertools


path_is_file = os.path.isfile
path_is_dir = os.path.isdir
path_exist = os.path.exists
path_dirname = os.path.dirname
path_basename = os.path.basename
path_common = os.path.commonpath
path_common_prefix = os.path.commonprefix
path_join = os.path.join
path_user_tilde = os.path.expanduser
path_env_var = os.path.expandvars
path_split = os.path.split
path_split_ext = os.path.splitext
path_absolute = os.path.abspath
path_real = os.path.realpath
path_relative = os.path.relpath
path_normalize = os.path.normpath
path_size = os.path.getsize
path_ctime = os.path.getctime
path_mtime = os.path.getmtime
