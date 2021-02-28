#!/usr/bin/env python3
# encoding=utf8
from .i1_qt import *
from .m_path import Path
from .. import i18n

i18n.auto_set()
tt = i18n.tt


class RenameDialog(Path):
    s = Str('\n'.join([str(i) for i in range(20)]))

    def default_traits_view(self):
        return View(
            Item(vn(self.full), label=tt('Source') + tt('Path'), style=tn.readonly,
                 editor=TextEditor(readonly_allow_selection=True)),
            Item(vn(self.s), style=tn.custom, editor=TextEditor(read_only=True)),
            title=f'{tt("Rename")} - {self.full}',
            resizable=True, width=0.5
        )
