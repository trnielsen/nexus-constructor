# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'translation.ui',
# licensing of 'translation.ui' applies.
#
# Created: Mon Jun 17 14:56:04 2019
#      by: pyside2-uic  running on PySide2 5.12.3
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_TranslationFrame(object):
    def setupUi(self, TranslationFrame):
        TranslationFrame.setObjectName("TranslationFrame")
        TranslationFrame.resize(400, 300)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(TranslationFrame)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setObjectName("mainLayout")
        self.groupBox = QtWidgets.QGroupBox(TranslationFrame)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.referenceTransformLabel = QtWidgets.QLabel(self.groupBox)
        self.referenceTransformLabel.setObjectName("referenceTransformLabel")
        self.horizontalLayout.addWidget(self.referenceTransformLabel)
        self.referenceTransformation = QtWidgets.QComboBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.referenceTransformation.sizePolicy().hasHeightForWidth())
        self.referenceTransformation.setSizePolicy(sizePolicy)
        self.referenceTransformation.setObjectName("referenceTransformation")
        self.horizontalLayout.addWidget(self.referenceTransformation)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.xLabel = QtWidgets.QLabel(self.groupBox)
        self.xLabel.setObjectName("xLabel")
        self.horizontalLayout_2.addWidget(self.xLabel)
        self.xCoordLineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.xCoordLineEdit.setObjectName("xCoordLineEdit")
        self.horizontalLayout_2.addWidget(self.xCoordLineEdit)
        self.yLabel = QtWidgets.QLabel(self.groupBox)
        self.yLabel.setObjectName("yLabel")
        self.horizontalLayout_2.addWidget(self.yLabel)
        self.yCoordLineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.yCoordLineEdit.setObjectName("yCoordLineEdit")
        self.horizontalLayout_2.addWidget(self.yCoordLineEdit)
        self.zLabel = QtWidgets.QLabel(self.groupBox)
        self.zLabel.setObjectName("zLabel")
        self.horizontalLayout_2.addWidget(self.zLabel)
        self.zCoordLineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.zCoordLineEdit.setObjectName("zCoordLineEdit")
        self.horizontalLayout_2.addWidget(self.zCoordLineEdit)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.verticalLayout_4.addLayout(self.verticalLayout_3)
        self.mainLayout.addWidget(self.groupBox)
        self.verticalLayout_2.addLayout(self.mainLayout)

        self.retranslateUi(TranslationFrame)
        QtCore.QMetaObject.connectSlotsByName(TranslationFrame)

    def retranslateUi(self, TranslationFrame):
        TranslationFrame.setWindowTitle(QtWidgets.QApplication.translate("TranslationFrame", "Frame", None, -1))
        self.groupBox.setTitle(QtWidgets.QApplication.translate("TranslationFrame", "Translation", None, -1))
        self.referenceTransformLabel.setText(QtWidgets.QApplication.translate("TranslationFrame", "Reference transformation", None, -1))
        self.xLabel.setText(QtWidgets.QApplication.translate("TranslationFrame", "x", None, -1))
        self.yLabel.setText(QtWidgets.QApplication.translate("TranslationFrame", "y", None, -1))
        self.zLabel.setText(QtWidgets.QApplication.translate("TranslationFrame", "z", None, -1))

