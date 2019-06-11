#!/usr/bin/env python

from PySide2.QtCore import Qt, QSize, QPoint
from PySide2.QtWidgets import QApplication, QTreeView, QHBoxLayout, QStyledItemDelegate, QFrame, QPushButton, QVBoxLayout, QSizePolicy, QLabel, QLineEdit
from nexus_constructor.component_tree_model import *
from nexus_constructor.component_wrapper import *
from PySide2.QtGui import QPixmap, QRegion

class RotateSettingsFrame(QFrame):
    def __init__(self, data, parent):
        self.data = data
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.pos_layout = QHBoxLayout()
        self.x_label = QLabel("x:", self)
        self.y_label = QLabel("y:", self)
        self.z_label = QLabel("z:", self)
        self.x_field = QLineEdit(str(data.X), self)
        self.y_field = QLineEdit(str(data.Y), self)
        self.z_field = QLineEdit(str(data.Z), self)
        self.setLayout(self.main_layout)
        rot_label = QLabel("Rotation", self)
        self.main_layout.addWidget(rot_label)
        self.main_layout.addLayout(self.pos_layout)
        self.pos_layout.addWidget(self.x_label)
        self.pos_layout.addWidget(self.x_field)
        self.pos_layout.addWidget(self.y_label)
        self.pos_layout.addWidget(self.y_field)
        self.pos_layout.addWidget(self.z_label)
        self.pos_layout.addWidget(self.z_field)
        self.angle_layout = QHBoxLayout()
        self.angle_label = QLabel("angle (degrees):", self)
        self.angle_field = QLineEdit(str(data.Angle), self)
        self.angle_layout.addWidget(self.angle_label)
        self.angle_layout.addWidget(self.angle_field)
        self.main_layout.addLayout(self.angle_layout)
        self.x_field.editingFinished.connect(self.XValChanged)
        self.y_field.editingFinished.connect(self.YValChanged)
        self.z_field.editingFinished.connect(self.ZValChanged)

    def XValChanged(self):
            self.data.X = self.x_field.text()

    def YValChanged(self):
            self.data.Y = self.y_field.text()

    def ZValChanged(self):
            self.data.Z = self.z_field.text()

class TranslateSettingsFrame(QFrame):
    def __init__(self, data, parent):
        self.data = data
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.pos_layout = QHBoxLayout()
        self.x_label = QLabel("x:", self)
        self.y_label = QLabel("y:", self)
        self.z_label = QLabel("z:", self)
        self.x_field = QLineEdit(str(data.X), self)
        self.y_field = QLineEdit(str(data.Y), self)
        self.z_field = QLineEdit(str(data.Z), self)
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(QLabel("Translation", self))
        self.main_layout.addLayout(self.pos_layout)
        self.pos_layout.addWidget(self.x_label)
        self.pos_layout.addWidget(self.x_field)
        self.pos_layout.addWidget(self.y_label)
        self.pos_layout.addWidget(self.y_field)
        self.pos_layout.addWidget(self.z_label)
        self.pos_layout.addWidget(self.z_field)
        self.x_field.editingFinished.connect(self.XValChanged)
        self.y_field.editingFinished.connect(self.YValChanged)
        self.z_field.editingFinished.connect(self.ZValChanged)

    def XValChanged(self):
        self.data.X = self.x_field.text()

    def YValChanged(self):
        self.data.Y = self.y_field.text()

    def ZValChanged(self):
        self.data.Z = self.z_field.text()

class ComponentEditorDelegate(QStyledItemDelegate):
    SettingsFrameMap = {Rotation:RotateSettingsFrame, Translation:TranslateSettingsFrame}
    frameSize = QSize(30, 10)

    def __init__(self, parent):
        super().__init__(parent)

    def getFrame(self, value):
        frame = QFrame()
        frame.setAutoFillBackground(True)
        SizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        SizePolicy.setHorizontalStretch(0)
        SizePolicy.setVerticalStretch(0)

        AltSizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        AltSizePolicy.setVerticalStretch(0)

        frame.setSizePolicy(SizePolicy)
        frame.layout = QVBoxLayout()
        frame.layout.setContentsMargins(0,0,0,0)
        frame.setLayout(frame.layout)
        if issubclass(type(value), Cp.Component):
            frame.label = QLabel(str(value), frame)
            frame.layout.addWidget(frame.label)
        elif type(value) is Cp.TransformationList:
            frame.label = QLabel(str(value), frame)
            frame.layout.addWidget(frame.label)
        elif issubclass(type(value), Cp.Transformation):
            frame.editor_header_layout = QHBoxLayout()
            label = QLabel("Name", frame)
            label.setSizePolicy(SizePolicy)
            frame.editor_header_layout.addWidget(label)
            frame.editor_header_layout.setContentsMargins(0, 0, 0, 0)
            frame.component_name = QLineEdit(value.Name, frame)
            frame.component_name.setSizePolicy(AltSizePolicy)
            line = QFrame(frame)
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Sunken)
            frame.editor_header_layout.addWidget(frame.component_name)
            frame.editor_header_layout.addWidget(line)
            frame.edit_btn = QPushButton("Edit", frame)
            frame.edit_btn.setSizePolicy(SizePolicy)
            frame.editor_header_layout.addWidget(frame.edit_btn)
            frame.layout.addLayout(frame.editor_header_layout)
            frame.editor_header_layout.setEnabled(False)
            line2 = QFrame(frame)
            line2.setFrameShape(QFrame.HLine)
            line2.setFrameShadow(QFrame.Sunken)
            line2.setContentsMargins(0, 0, 0, 0)
            frame.setContentsMargins(0, 0, 0, 0)
            frame.layout.setContentsMargins(0, 0, 0, 0)
            frame.layout.addWidget(line2)
            frame.edit_frame = self.SettingsFrameMap[type(value)](value, frame)
            frame.layout.addWidget(frame.edit_frame, Qt.AlignTop)
            frame.edit_frame.setEnabled(False)
            frame.component_name.setEnabled(False)
        else:
            raise Exception("Unknown element type in tree view.")

        return frame

    def paint(self, painter, option, index):
        model = index.model()
        value = model.data(index, Qt.DisplayRole)
        frame = self.getFrame(value)
        frame.setFixedSize(option.rect.size())
        ratio = self.parent().devicePixelRatioF()
        pixmap = QPixmap(frame.size() * ratio)
        pixmap.setDevicePixelRatio(ratio)
        frame.render(pixmap, QPoint(), QRegion())
        painter.drawPixmap(option.rect, pixmap)

    def createEditor(self, parent, option, index):
        model = index.model()
        value = model.data(index, Qt.DisplayRole)
        frame = self.getFrame(value)
        frame.setParent(parent)
        self.frameSize = frame.sizeHint()
        return frame

    def setEditorData(self, editorWidget, index):
        model = index.model()
        editorWidget.edit_frame.setEnabled(True)
        editorWidget.component_name.setEnabled(True)
        editorWidget.edit_btn.setText("Done")
        #spinBox.editor.setText(value["data"].Name)

    def setModelData(self, editorWidget, model, index):
        editorWidget.edit_frame.setEnabled(False)
        editorWidget.component_name.setEnabled(False)
        editorWidget.edit_btn.setText("Edit")

    def sizeHint(self, option, index):
        model = index.model()
        value = model.data(index, Qt.DisplayRole)
        frame = self.getFrame(value)
        return frame.sizeHint()

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class ComponentTreeView(QTreeView):
    def __init__(self, parent = None):
        super().__init__(parent)

    def dragMoveEvent(self, event):
        print("dragMoveEvent")
        event.setDropAction(Qt.MoveAction)
        event.accept()

    def dragLeaveEvent(self, event: PySide2.QtGui.QDragLeaveEvent):
        print("dragLeaveEvent")

    def dragEnterEvent(self, event: PySide2.QtGui.QDragEnterEvent):
        print("dragEnterEvent")
