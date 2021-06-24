#!/usr/bin/env python3
from PySide2.QtCore import QItemSelectionModel


class EzQModelView:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.setModel(self.model)
        self.selection_model: QItemSelectionModel = self.view.selectionModel()
        self.index = self.model.index
        self.data = self.model.data

    def connect_signal_selection_changed(self, callee_as_slot):
        self.selection_model.selectionChanged.connect(callee_as_slot)
        return self

    def connect_signal_current_changed(self, callee_as_slot):
        self.selection_model.currentChanged.connect(callee_as_slot)
        return self

    @property
    def last_row_index(self):
        return self.model.rowCount() - 1

    @property
    def last_col_index(self):
        return self.model.columnCount() - 1

    def set_current_index(self, index):
        self.view.setCurrentIndex(index)
        return self
