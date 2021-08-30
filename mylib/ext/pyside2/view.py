#!/usr/bin/env python3
from PySide2.QtCore import QItemSelectionModel, QAbstractItemModel
from PySide2.QtWidgets import QAbstractItemView, QScroller

from mylib.ext.pyside2.signal import ez_qt_signal_connect


def ez_qt_view_left_mouse_gesture_scrolling(obj):
    QScroller.grabGesture(obj.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
    return QScroller.scroller(obj)


def ez_qt_view_pixel_scrolling(view: QAbstractItemView):
    view.setVerticalScrollMode(view.ScrollPerPixel)


class EzQtModelViewWrapper:
    EditTriggerEnum = QAbstractItemView.EditTrigger

    def __init__(self, model, view):
        self.view: QAbstractItemView = view
        self.view.setModel(model)
        self.__model = self.view.model()

    @property
    def selection_model(self):
        return self.view.selectionModel()

    def set_delegate(self, delegate=None, for_row=None, for_col=None):
        if delegate:
            self.view.setItemDelegate(delegate)
        if for_row:
            self.view.setItemDelegateForRow(for_row)
        if for_col:
            self.view.setItemDelegateForColumn(for_col)
        return self

    def set_alternating_row(self, enable=True):
        self.view.setAlternatingRowColors(enable)
        return self

    def signal_connect_selection_changed(self, callee_as_slot):
        ez_qt_signal_connect(self.selection_model.selectionChanged, callee_as_slot)
        return self

    def signal_connect_current_changed(self, callee_as_slot):
        ez_qt_signal_connect(self.selection_model.selectionChanged, callee_as_slot)
        return self

    @property
    def model(self):
        return self.__model

    @model.setter
    def model(self, value):
        self.set_model(value)

    def set_model(self, model):
        self.view.setModel(model)
        self.__model = model
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
