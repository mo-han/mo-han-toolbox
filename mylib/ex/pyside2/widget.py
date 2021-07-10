#!/usr/bin/env python3
from PySide2.QtCore import QPoint
from PySide2.QtGui import *
from PySide2.QtGui import QPainter, QRegion
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtWidgets import QWidget

from mylib import easy
from mylib.ex.pyside2.signal import *
from mylib.ex.pyside2.style import *


def qt_text_label(s: str, parent=None, style=None):
    lb = QLabel(parent)
    lb.setText(s)
    if style:
        lb.setStyleSheet(ez_qss(style))
    return lb


class EzQtWidgetMixin:
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
        self.setStyleSheet(ez_qss(style, selector))
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

    @easy.contextlib.contextmanager
    def ctx_delete_later(self: QWidget):
        yield self
        self.deleteLater()


class EzQtApplication(QApplication, EzQtWidgetMixin):
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


class EzQtPushButton(QPushButton, EzQtWidgetMixin):
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


class EzQtLabel(QLabel, EzQtWidgetMixin):
    pass


class EzQtDelegateWidgetMixin:
    __qt_painter__: QPainter

    @easy.contextlib.contextmanager
    def ctx_painter_translate_offset(self, *offset):
        self.__qt_painter__.save()
        self.__qt_painter__.translate(*offset)
        yield self.__qt_painter__
        self.__qt_painter__.restore()

    def set_painter(self, painter):
        self.__qt_painter__ = painter
        return self

    def draw_widget(self, flags=QWidget.DrawChildren):
        painter = self.__qt_painter__
        self: QWidget
        self.render(painter, QPoint(), QRegion(), flags)

    def draw_widget_snap(self):
        painter = self.__qt_painter__
        self: QWidget
        painter.drawPixmap(QPoint(), self.grab())

    def draw(self, *offset):
        with self.ctx_painter_translate_offset(*offset):
            self.draw_widget()
