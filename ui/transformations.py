# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'transformations.ui',
# licensing of 'transformations.ui' applies.
#
# Created: Mon Jun 17 14:56:05 2019
#      by: pyside2-uic  running on PySide2 5.12.3
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_TransformationFrame(object):
    def setupUi(self, TransformationFrame):
        TransformationFrame.setObjectName("TransformationFrame")
        TransformationFrame.resize(342, 120)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(TransformationFrame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setObjectName("mainLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(TransformationFrame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(TransformationFrame)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.editButton = QtWidgets.QPushButton(TransformationFrame)
        self.editButton.setObjectName("editButton")
        self.horizontalLayout.addWidget(self.editButton)
        self.mainLayout.addLayout(self.horizontalLayout)
        self.line = QtWidgets.QFrame(TransformationFrame)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.mainLayout.addWidget(self.line)
        self.verticalLayout_2.addLayout(self.mainLayout)

        self.retranslateUi(TransformationFrame)
        QtCore.QMetaObject.connectSlotsByName(TransformationFrame)

    def retranslateUi(self, TransformationFrame):
        TransformationFrame.setWindowTitle(QtWidgets.QApplication.translate("TransformationFrame", "Frame", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("TransformationFrame", "Name", None, -1))
        self.editButton.setText(QtWidgets.QApplication.translate("TransformationFrame", "Edit", None, -1))

