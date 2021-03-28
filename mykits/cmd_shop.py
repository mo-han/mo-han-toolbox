#!/usr/bin/env python3
from mylib import fstk_lite
from mylib.ez import *

dn, bn, ext = fstk_lite.split_dirname_basename_ext(__file__)
subs = {}
with fstk_lite.ctx_pushd(dn):
    for fp in next(os.walk('.'))[-1]:
        match = re.match(rf'({bn})_(.+)\.py', fp)
        if not match:
            continue
        module_name = match.group(2)
        module = python_module_from_filepath(module_name, fp)
        subs[module_name] = module
