#!/usr/bin/env python3
import contextlib

from PySide2.QtCore import QAbstractListModel, Signal, QModelIndex, Qt
from PySide2.QtGui import QStandardItemModel
from PySide2.QtWidgets import QApplication

from mylib.easy import FirstCountLastStop, T


class InternalItemsEzQListModel(QAbstractListModel):
    items_changed = Signal()
    an_item_changed = Signal(QModelIndex)

    def __init__(self, parent=None, batch_size=100, items_header='Items'):
        super().__init__(parent)
        self._batch_size = batch_size
        self._current_size = 0
        self._items = []
        self.items_header = items_header
        self.data_getter_mapping = {Qt.DisplayRole: self.get_display_data, Qt.BackgroundRole: self.get_background_data}
        self.items_changed.connect(self.layoutChanged)

    @property
    def items_size(self):
        return len(self._items)

    @contextlib.contextmanager
    def ctx_change_layout(self):
        self.layoutAboutToBeChanged.emit()
        yield
        self.layoutChanged.emit()

    @contextlib.contextmanager
    def ctx_change_items(self):
        yield
        self.items_changed.emit()

    @contextlib.contextmanager
    def ctx_change_an_item(self, index):
        yield
        self.an_item_changed.emit(index)

    @staticmethod
    def convert_model_index_to_item_index(index: QModelIndex):
        return index.row()

    def clear_items(self):
        with self.ctx_change_layout():
            with self.ctx_change_items():
                self._items.clear()
                self._current_size = 0
        return self

    def append_item(self, x):
        with self.ctx_change_layout():
            with self.ctx_change_items():
                self._items.append(x)
        return self

    def insert_item(self, index: QModelIndex, x):
        with self.ctx_change_layout():
            with self.ctx_change_items():
                self._items.insert(self.convert_model_index_to_item_index(index), x)
        return self

    def extend_items(self, items: T.Iterable):
        with self.ctx_change_layout():
            with self.ctx_change_items():
                self._items.extend(items)
        return self

    def get_item(self, index: QModelIndex):
        return self._items[self.convert_model_index_to_item_index(index)]

    def set_item(self, index: QModelIndex, value):
        with self.ctx_change_an_item(index):
            self._items[self.convert_model_index_to_item_index(index)] = value
            self.dataChanged.emit(index, index)
        return self

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        n = self._current_size
        if n <= self.items_size:
            return n
        else:
            self._current_size = self.items_size
            return self.items_size

    @staticmethod
    def get_none_data(index):
        return None

    def get_display_data(self, index: QModelIndex):
        return self.convert_item_to_display_data(self._items[index.row()])

    @staticmethod
    def convert_item_to_display_data(item):
        return str(item)

    @staticmethod
    def get_background_data(index: QModelIndex):
        palette = QApplication.palette()
        return palette.alternateBase() if index.row() % 2 else palette.base()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if self.items_size <= index.row() < 0:
            return None
        return self.data_getter_mapping.get(role, self.get_none_data)(index)

    @staticmethod
    def convert_edit_data_to_item(data):
        return eval(data)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if role != Qt.EditRole:
            return False
        row = index.row()
        if self.items_size <= row < 0:
            return False
        self._items[row] = self.convert_edit_data_to_item(value)
        self.dataChanged.emit(index, index)
        # print(self.setData.__name__, row, self._items[row], self.data(index))
        return True

    def headerData(self, section, orientation, role=None):
        if orientation != Qt.Horizontal:
            return None
        if section != 0:
            return None
        if role != Qt.DisplayRole:
            return None
        return self.items_header

    def canFetchMore(self, parent: QModelIndex = QModelIndex()):
        if parent.isValid():
            return False
        return self._current_size < self.items_size

    def fetchMore(self, parent: QModelIndex = QModelIndex()):
        if parent.isValid():
            return
        fcls = FirstCountLastStop().set_first_and_total(self._current_size,
                                                        min(self.items_size - self._current_size, self._batch_size))
        self.beginInsertRows(parent, fcls.first, fcls.last)
        self.endInsertRows()
        self._current_size += fcls.total
