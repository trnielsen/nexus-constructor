from functools import partial

import numpy as np
import typing
from PySide2.QtCore import QModelIndex, QAbstractTableModel, Qt, QAbstractItemModel
from PySide2.QtWidgets import (
    QWidget,
    QGridLayout,
    QTableView,
    QToolBar,
    QAction,
    QAbstractItemView,
    QItemDelegate,
    QStyleOptionViewItem,
    QLineEdit,
)

from nexus_constructor.ui_utils import validate_line_edit
from nexus_constructor.validators import NumpyDTypeValidator


class ArrayDatasetTableWidget(QWidget):
    """
    Wrapper over a QTableView with buttons to add and delete rows/columns
    """

    def __init__(self, type: np.dtype = np.byte, parent=None):
        super().__init__(parent)
        self.model = ArrayDatasetTableModel(dtype=type, parent=self)
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.view.setItemDelegate(ValueDelegate(type, parent))

        self.setLayout(QGridLayout())
        self.toolbox = QToolBar()
        self.add_row_button = QAction(text="➕ Add Row")
        self.add_row_button.triggered.connect(self.model.add_row)
        self.remove_row_button = QAction(text="➖ Remove Row")
        self.remove_row_button.triggered.connect(partial(self.model.delete_index, True))
        self.add_column_button = QAction(text="➕ Add Column")
        self.add_column_button.triggered.connect(self.model.add_column)
        self.remove_column_button = QAction(text="➖ Remove Column")
        self.remove_column_button.triggered.connect(
            partial(self.model.delete_index, False)
        )

        self.toolbox.addAction(self.add_row_button)
        self.toolbox.addAction(self.remove_row_button)
        self.toolbox.addAction(self.add_column_button)
        self.toolbox.addAction(self.remove_column_button)

        self.layout().addWidget(self.toolbox)
        self.layout().addWidget(self.view)


class ArrayDatasetTableModel(QAbstractTableModel):
    def __init__(self, dtype: np.dtype, parent: ArrayDatasetTableWidget):
        super().__init__()
        self.setParent(parent)
        self.int_array = np.array([[0]], dtype=dtype)

    @property
    def array(self) -> np.ndarray:
        return self.int_array

    @array.setter
    def array(self, array: np.ndarray):
        if array.ndim == 1:
            self.int_array = np.array([array])
        else:
            self.int_array = array

    def update_array_dtype(self, dtype: np.dtype):
        """
        Updates the array dataset type.
        If there is existing data in the array, it tries to cast the values to the new dtype.
        If not or if numpy is unable to cast the values, a new array is created.
        :param dtype: The new dataset type to set the array to.
        """
        self.beginResetModel()
        try:
            self.int_array = np.array(self.int_array.data, dtype=dtype)
        except ValueError:
            self.int_array = np.array([[0]], dtype=dtype)
        self.parent().view.itemDelegate().dtype = dtype
        self.endResetModel()

    def add_row(self):
        self.beginResetModel()
        self.int_array = np.resize(self.int_array, (self.int_array.shape[0] + 1, self.int_array.shape[1]))
        self.endResetModel()

    def add_column(self):
        self.beginResetModel()
        self.int_array = np.column_stack(
            (self.int_array, np.zeros(np.shape(self.int_array)[0], dtype=self.int_array.dtype))
        )
        self.endResetModel()

    def delete_index(self, is_row: bool):
        """
        Removes either selected rows or columns depending on is_row
        :param is_row: bool, if true remove rows, if false remove columns
        """
        self.beginResetModel()
        for index in self.parent().view.selectedIndexes():
            if is_row and self.int_array.shape[0] <= 1:
                return
            elif not is_row and self.int_array.shape[1] <= 1:
                return
            self.int_array = np.delete(
                self.int_array,
                (index.row() if is_row else index.column()),
                axis=int(not is_row),
            )
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = ...) -> int:
        """
        Dictates how many rows there are in the table.
        :param parent: Unused.
        :return: Number of elements in each dimension.
        """
        return self.int_array.shape[0]

    def columnCount(self, parent: QModelIndex = ...) -> int:
        """
        Dictates how many columns there are in the table.
        :param parent: Unused.
        :return: Number of dimensions there are in the array.
        """
        if self.int_array.ndim == 1:
            return 1
        return self.int_array.shape[1]

    def data(self, index: QModelIndex, role: int = ...) -> str:
        if role == Qt.DisplayRole or role == Qt.EditRole:
            value = self.int_array[index.row()][index.column()]
            return str(value)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return (
            super(ArrayDatasetTableModel, self).flags(index)
            | Qt.ItemIsEditable
            | Qt.ItemIsEnabled
            | Qt.ItemIsSelectable
        )

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = ...  # noqa: W504
    ) -> typing.Any:
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if orientation == Qt.Vertical:
                return f"{section:d}"
            if orientation == Qt.Horizontal:
                return f"{section:d}"
        return None

    def setData(self, index: QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if index.isValid() and role == Qt.EditRole and value:
            self.int_array[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False


class ValueDelegate(QItemDelegate):
    def __init__(self, dtype, parent):
        super().__init__(parent)
        self.dtype = dtype

    def commit(self, editor):
        """
        Calls the commitData signal to update the model when text is being edited rather than when it has finished being edited and loses focus.
        :param editor: The line edit in the item delegate.
        """
        self.commitData.emit(editor)

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        editor = QLineEdit(parent)
        editor.setValidator(NumpyDTypeValidator(self.dtype))
        editor.validator().is_valid.connect(
            partial(
                validate_line_edit,
                editor,
                tooltip_on_reject="Not valid for the selected dtype",
            )
        )

        # Update the model when the item is being edited rather than when it has lost focus and finished.
        editor.editingFinished.connect(partial(self.commit, editor))
        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        value = index.model().data(index, Qt.EditRole)
        editor.setText(value)

    def setModelData(
        self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex
    ):
        value = editor.text()
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(
        self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        editor.setGeometry(option.rect)
