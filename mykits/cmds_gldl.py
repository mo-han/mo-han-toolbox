#!/usr/bin/env python3
from mylib.ex.console_app import *

apr = ArgumentParserRigger()
an = apr.an


class GalleryDlCLIArgs(CLIArgumentsList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add('gallery-dl', v=True, R=10,)