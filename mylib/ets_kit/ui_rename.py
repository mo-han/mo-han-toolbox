#!/usr/bin/env python3
# encoding=utf8
from .i1_traitsui_qt import *
from .m_path import Path
from ..shards import i18n

i18n.preset_alpha()
tt = i18n.tt


class RenameDialog(Path):
    info_src = tn.info_src = Str(tn.info_src * 100)
    info_text = tn.info_text = Str('\n'.join([str(i) for i in range(20)]))

    traits_view = View(
        VGroup(
            Item(' '),
            HGroup(
                Item(' '),
                Item(vn(self.full), label=f"{tt('Source')} {tt('Path')}", editor=TextEditor(read_only=True)),
                # Item(' '),
            ),
            VGroup(
                Item(tn.info_src, show_label=False, editor=TextEditor(read_only=True)),
                Item(tn.info_text, show_label=False, style='custom', editor=TextEditor(read_only=True)),
                show_border=True,
            ),
            Item(vn(self.dirname), show_label=False),
            HGroup(
                Item(vn(self.stem), show_label=False, has_focus=True, width=0.9),
                Item(vn(self.extension), show_label=False, width=0.1),
            ),
        ),

        title=f'{tt("Rename")} - {self.full}',
        resizable=True, width=0.5
    )
