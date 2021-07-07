#!/usr/bin/env python3
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *

from mylib.ex.pyside2.signal import *
from mylib.ex.pyside2.style import *


def qt_text_label(s: str, parent=None, style=None):
    lb = QLabel(parent)
    lb.setText(s)
    if style:
        lb.setStyleSheet(ez_qt_style_sheet(style))
    return lb


class MixinForQWidget:
    @property
    def connections(self):
        try:
            return self.__signal_connections
        except AttributeError:
            self.__signal_connections = {}
            return self.__signal_connections

    def signal_reconnect(self, signal, new=None, old=None):
        self.connections[signal] = ez_qt_signal_reconnect(signal, new, old)

    def get_qss(self: QWidget):
        return self.styleSheet()

    def set_qss(self: QWidget, style, selector=None):
        self.setStyleSheet(ez_qt_style_sheet(style, selector))
        return self

    @property
    def qss(self):
        return self.get_qss()

    @qss.setter
    def qss(self: QWidget, value):
        self.set_qss(value)

    def new_shortcut(self, key_sequence: QKeySequence,
                     connect_to: T.Union[T.Callable[..., T.Any], T.Iterable[T.Callable[..., T.Any]]],
                     parent_widget=...):
        shortcut = QShortcut(key_sequence, self if parent_widget is ... else parent_widget, None)
        if connect_to:
            ez_qt_signal_connect(shortcut.activated, connect_to)
        return shortcut


class EzQtApplication(QApplication, MixinForQWidget):
    def set_qt_translate(self, locale_name: str = None, filename_in_translations: str = None,
                         parent=...):
        translator = QTranslator(self if parent is ... else parent)
        if locale_name:
            translator.load(f'qt_{locale_name.replace("-", "_")}.qm',
                            QLibraryInfo.location(QLibraryInfo.TranslationsPath))
        if filename_in_translations:
            translator.load(filename_in_translations, QLibraryInfo.location(QLibraryInfo.TranslationsPath))
        self.installTranslator(translator)
        return self


class EzQtPushButton(QPushButton, MixinForQWidget):
    @property
    def on_click(self):
        return self.connections.get(self.clicked, [])

    @on_click.setter
    def on_click(self, value):
        self.signal_reconnect(self.clicked, value)

    @Slot()
    def enable(self):
        self.setEnabled(True)
        return self

    @Slot()
    def disable(self):
        self.setDisabled(True)
        return self


class EzQtLabel(QLabel, MixinForQWidget):
    pass
