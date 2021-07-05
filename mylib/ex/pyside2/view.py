#!/usr/bin/env python3
from PySide2.QtCore import QItemSelectionModel, QAbstractItemModel
from PySide2.QtWidgets import QAbstractItemView, QScroller
from mylib.ex.pyside2.signal import ez_qt_signal_connect


def ez_qt_set_left_mouse_gesture_scrolling(obj):
    QScroller.grabGesture(obj.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
    return QScroller.scroller(obj)


def ez_qt_set_pixel_scrolling(view: QAbstractItemView):
    view.setVerticalScrollMode(view.ScrollPerPixel)


class EzQtModelViewWrapper:
    EditTriggerEnum = QAbstractItemView.EditTrigger

    def __init__(self, model, view):
        self.model: QAbstractItemModel = model
        self.view: QAbstractItemView = view
        self.view.setModel(self.model)
        self.selection_model: QItemSelectionModel = self.view.selectionModel()
        self.index = self.model.index
        self.data = self.model.data

    def connect_signal_selection_changed(self, callee_as_slot):
        ez_qt_signal_connect(self.selection_model.selectionChanged, callee_as_slot)
        return self

    def connect_signal_current_changed(self, callee_as_slot):
        ez_qt_signal_connect(self.selection_model.selectionChanged, callee_as_slot)
        return self

    @property
    def last_row_index(self):
        return self.model.rowCount() - 1

    @property
    def last_col_index(self):
        return self.model.columnCount() - 1

    @property
    def current_index(self):
        return self.view.currentIndex()

    @current_index.setter
    def current_index(self, value):
        self.view.setCurrentIndex(value)

    @property
    def edit_triggers(self):
        return self.view.editTriggers()

    @edit_triggers.setter
    def edit_triggers(self, value):
        self.view.setEditTriggers(value)
