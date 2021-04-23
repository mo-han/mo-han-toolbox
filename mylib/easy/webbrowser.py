#!/usr/bin/env python3
from webbrowser import *
from webbrowser import BackgroundBrowser

from . import *


def get_web_browser(name: str, path: str):
    register(name, None, BackgroundBrowser(path))
    return get(name)


def get_firefox(path=None):
    name = 'firefox'
    if not path:
        if os.name == 'nt':
            mozilla_firefox = 'Mozilla Firefox'
            make_call = functools.partial(ACall, shutil.which, name)
            path = ALotCall(
                *[make_call(path=path_join(os.environ[env_var], mozilla_firefox)) for env_var in
                  ['ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)']],
                make_call(),
            ).any_result(ignore_exceptions=Exception)
        else:
            path = shutil.which(name)
    if not path:
        raise FileNotFoundError(name)
    return get_web_browser(name, path)
