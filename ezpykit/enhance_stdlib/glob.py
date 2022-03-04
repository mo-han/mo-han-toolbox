#!/usr/bin/env python3
from glob import *
from urllib.parse import urlparse
from ezpykit.enhance_builtin import ezstr


def iglob_url(glob_url, **kwargs):
    u = urlparse(glob_url)
    if u.scheme != 'glob':
        raise ValueError('URL scheme', 'glob', u.scheme)
    if u.netloc not in ('', 'localhost'):
        raise NotImplementedError('remote glob')
    return iglob(ezstr.removeprefix(u.path, '/'))
