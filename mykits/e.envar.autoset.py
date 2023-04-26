#!/usr/bin/env python3
from pprint import pprint

from oldezpykit.allinone import *

locallib_env = os.get_dirname(__file__)
locallib = os.get_dirname(locallib_env)

envar = {
    'locallib': locallib,
}
for p in ('env', 'etc', 'usr'):
    envar[f'locallib_{p}'] = os.join_path(locallib, p)
for p in ('env', 'etc', 'dl'):
    envar[f'locallib_usr{p}'] = os.join_path(locallib, 'usr', p)

paths = [
    os.join_path(locallib, 'usr', 'env'),
    os.join_path(locallib, 'env'),
    os.join_path(locallib, 'env', '_win64'),
    os.join_path(locallib, 'env', '_winbin'),
]

os.EnVarKit.save(envar)
pprint(envar)
os.EnVarKit.save_path(insert=paths)
pprint(paths)
