#!/usr/bin/env python3
# encoding=utf8

import os

os.environ['pythonpath'] = '.'
cmd = {'nt': 'start /max cmd'}
os.system(cmd[os.name])
