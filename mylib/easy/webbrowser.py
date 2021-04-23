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
            for caller in (
                    ACall(shutil.which, name),
                    ACall(shutil.which, name, path=path_join(os.environ['ProgramFiles'], mozilla_firefox)),
                    ACall(shutil.which, name, path=path_join(os.environ['ProgramW6432'], mozilla_firefox)),
                    ACall(shutil.which, name, path=path_join(os.environ['ProgramFiles(x86)'], mozilla_firefox)),
            ):
                try:
                    path = caller.get()
                    if path:
                        break
                except:
                    continue
        else:
            path = shutil.which(name)
    if not path:
        raise FileNotFoundError(name, path)
    return get_web_browser(name, path)
