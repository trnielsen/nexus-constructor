#!/usr/bin/env python

from nexus_constructor.component_tree_model import *
from PySide2.QtCore import QAbstractItemModel
from PySide2.QtCore import QAbstractItemModel, QModelIndex, Qt, QMimeData
import PySide2
import typing
import nexus_constructor.test_components as Cp

class ComponentTreeModel(QAbstractItemModel):
    def __init__(self, data, parent=None):
        super(ComponentTreeModel, self).__init__(parent)
        self.rootItem = data

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return item
        elif role == Qt.SizeHintRole:
            return

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        item = index.internalPointer()
        if issubclass(type(item), Cp.Component):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif type(item) is Cp.TransformationList:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsDragEnabled


    def mimeData(self, indexes: typing.List[int]) -> PySide2.QtCore.QMimeData:
        mimeData = QMimeData()
        mimeData.setData("test_type", bytearray("no_mime".encode("utf8")))
        mimeData.data_pointers = []
        for itm in indexes:
            mimeData.data_pointers.append(itm.internalPointer())
        return mimeData

    def mimeTypes(self):
        return ["test_type"]

    def supportedDropActions(self) -> PySide2.QtCore.Qt.DropActions:
        return Qt.DropAction.MoveAction

    def dropMimeData(self, data: PySide2.QtCore.QMimeData, action: PySide2.QtCore.Qt.DropAction, row: int, column: int, parent: PySide2.QtCore.QModelIndex):
        TgtNode = parent.internalPointer()
        if type(TgtNode) is list:
            for i in range(len(data.data_pointers)):
                cData = data.data_pointers[i]
                oldDataParent = cData.parentItem
                oldDataParent.childItems.remove(cData)
                cData.parentItem = TgtNode
                if (row >= 0):
                    TgtNode.childItems.insert(row, cData)
                else:
                    TgtNode.childItems.append(cData)
                self.dataChanged.emit(QModelIndex(), QModelIndex())
                self.layoutChanged.emit()
                return True
        return False

    def dropEvent(self, event: PySide2.QtGui.QDropEvent):
        print("Done dropping")

    def headerData(self, section, orientation, role):
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        if type(parentItem) is list or type(parentItem) is Cp.TransformationList:
            childItem = parentItem[row]
        elif issubclass(type(parentItem), Cp.Component):
            childItem = parentItem.Transformations
        if childItem is not None:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        if issubclass(type(childItem), Cp.Component):
            parentItem = self.rootItem
        elif type(childItem) is Cp.TransformationList:
            parentItem = childItem.parent
            return self.createIndex(self.rootItem.index(parentItem), 0, parentItem)
        elif issubclass(type(childItem), Cp.Transformation):
            return self.createIndex(0, 0, childItem.Parent.Transformations)
        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        if type(parentItem) is list:
            return len(parentItem)
        elif type(parentItem) is Cp.TransformationList:
            return len(parentItem)
        elif issubclass(type(parentItem), Cp.Component):
            return 1
        return 0

if __name__ == '__main__':
    Sample = Cp.Component("Sample")
    Detector = Cp.Cylinder(Name = "Detector1")
    Detector.Transformations.append(Cp.Translation("DetMovement", Detector))
    Detector.Transformations.append(Cp.Rotation("DetRotation", Detector))
    ComponentList = []
    ComponentList.append(Sample)
    ComponentList.append(Detector)

    Model = ComponentTreeModel(Sample)