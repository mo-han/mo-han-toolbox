#!/usr/bin/env python3
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from .util import *
from .thread import *
from ... import easy
from ...easy import logging
from .const import *

_module_logger = logging.ez_get_logger(__name__, 'DEBUG')


def qt_text_label(s: str, parent=None, style=None):
    lb = QLabel(parent)
    lb.setText(s)
    if style:
        lb.setStyleSheet(ez_qss(style))
    return lb


@easy.contextlib.contextmanager
def ez_qt_ctx_delete_later(w):
    yield
    w.deleteLater()


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

    def add_shortcut(self, key_sequence: Qt.Key or str,
                     connect_to: T.Union[T.Callable[..., T.Any], T.Iterable[T.Callable[..., T.Any]]],
                     parent_widget=...):
        shortcut = QShortcut(QKeySequence(key_sequence), self if parent_widget is ... else parent_widget, None)
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
    str_fmt = '{}'

    def the_str_fmt(self, fmt: str):
        self.str_fmt = fmt
        return self

    def the_text(self, x=..., *args, **kwargs):
        if x is ...:
            return self.text()
        else:
            self.setText(self.str_fmt.format(x, *args, **kwargs))
            return self


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


class EzQtLogViewer(QPlainTextEdit, EzQtObjectMixin, logging.EzLoggingMixin):
    # html_fmt = '<font color="{color}"><pre>中文测试{{}}</pre></font>'
    html_fmt = '<pre style="font-family:consolas; color:{color}">{{}}</pre>'

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.set(read_only=True)
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)
        self.queue = easy.queue.Queue()
        self.handler = logging.QueueHandler(self.queue)
        self.flag_stop = False
        self.log_fmt = self.get_log_msg_fmt()

    def stop(self):
        self.flag_stop = True

    def get_log_msg_fmt(self):
        return {k: self.html_fmt.format(**v) for k, v in {
            logging.DEBUG: dict(color=EzColors.limegreen),
            logging.INFO: dict(color=EzColors.blue),
            logging.WARNING: dict(color=EzColors.darkorange),
            logging.ERROR: dict(color=EzColors.darkred),
            logging.CRITICAL: dict(color=EzColors.deeppink),
        }.items()}

    def set_format(self, fmt=None, date_fmt=None):
        formatter = logging.Formatter(fmt=fmt, datefmt=date_fmt)
        self.handler.setFormatter(formatter)
        return self

    def iter_msg(self):
        self.__logger__.debug('start')
        while True:
            if self.flag_stop:
                self.__logger__.debug('stop')
                break
            try:
                record: logging.LogRecord = self.queue.get(timeout=1)
            except queue.Empty:
                continue
            msg = self.log_fmt[record.levelno].format(self.handler.format(record).strip())
            yield msg

    def start(self):
        self.flag_stop = False
        EzQtThreadWorker(self.iter_msg).connect_signals(
            i_result=self.appendHtml).start_in_pool(self.thread_pool)
        return self
