#!/usr/bin/env python3
from PySide2.QtWidgets import *
from mylib.ex.pyside2.signal import *

from mylib.ex.pyside2.style import *


def qt_text_label(s: str, parent=None, style=None):
    lb = QLabel(parent)
    lb.setText(s)
    if style:
        lb.setStyleSheet(qt_style_sheet(style))
    return lb


class MixinForQWidget:
    @property
    def connections(self):
        try:
            return self._connections
        except AttributeError:
            self._connections = {}
            return self._connections

    def reconnect_signal(self, signal, new=None, old=None):
        self.connections[signal] = signal_reconnect(signal, new, old)


class EzQPushButton(QPushButton, MixinForQWidget):
    @property
    def on_click(self):
        return self.connections.get(self.clicked, [])

    @on_click.setter
    def on_click(self, value):
        self.reconnect_signal(self.clicked, value)
