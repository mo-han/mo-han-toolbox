#!/usr/bin/env python3
# encoding=utf8
from .u_path import *


class RenameDialog(Path):
    def default_traits_view(self):
        return View(
            Label(f'Old= {self.full}'),
            Item(vn(self.dirname), show_label=False),
            title=f'Rename - {self.full}',
            resizable=True, width=0.5
        )
