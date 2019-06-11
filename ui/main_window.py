# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_window.ui',
# licensing of 'main_window.ui' applies.
#
<<<<<<< HEAD:ui/mainwindow.py
# Created: Tue Jun 11 15:45:33 2019
=======
# Created: Mon Jun 10 10:13:15 2019
>>>>>>> afa41a065dd92dfce4496ef82ac5ca7f3195cbc7:ui/main_window.py
#      by: pyside2-uic  running on PySide2 5.12.3
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1287, 712)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setMinimumSize(QtCore.QSize(500, 0))
        self.tabWidget.setObjectName("tabWidget")
        self.componentsTab = QtWidgets.QWidget()
        self.componentsTab.setObjectName("componentsTab")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.componentsTab)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.componentsTabLayout = QtWidgets.QVBoxLayout()
        self.componentsTabLayout.setObjectName("componentsTabLayout")
        self.componentTreeView = QtWidgets.QTreeView(self.componentsTab)
        self.componentTreeView.setObjectName("componentTreeView")
        self.componentsTabLayout.addWidget(self.componentTreeView)
        self.verticalLayout_2.addLayout(self.componentsTabLayout)
        self.tabWidget.addTab(self.componentsTab, "")
        self.fileTab = QtWidgets.QWidget()
        self.fileTab.setObjectName("fileTab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.fileTab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget = QtWidgets.QWidget(self.fileTab)
        self.widget.setObjectName("widget")
        self.verticalLayout.addWidget(self.widget)
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.tabWidget.addTab(self.fileTab, "")
        self.gridLayout_3.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.sceneWidget = QtWidgets.QWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sceneWidget.sizePolicy().hasHeightForWidth())
        self.sceneWidget.setSizePolicy(sizePolicy)
        self.sceneWidget.setMinimumSize(QtCore.QSize(745, 0))
        self.sceneWidget.setObjectName("sceneWidget")
        self.gridLayout_3.addWidget(self.sceneWidget, 0, 1, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_3, 1, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar()
<<<<<<< HEAD:ui/mainwindow.py
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1287, 22))
=======
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1263, 19))
>>>>>>> afa41a065dd92dfce4496ef82ac5ca7f3195cbc7:ui/main_window.py
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionOpen_NeXus_file = QtWidgets.QAction(MainWindow)
        self.actionOpen_NeXus_file.setObjectName("actionOpen_NeXus_file")
        self.actionExport_to_NeXus_file = QtWidgets.QAction(MainWindow)
        self.actionExport_to_NeXus_file.setObjectName("actionExport_to_NeXus_file")
        self.actionExport_to_Filewriter_JSON = QtWidgets.QAction(MainWindow)
        self.actionExport_to_Filewriter_JSON.setObjectName("actionExport_to_Filewriter_JSON")
        self.menuFile.addAction(self.actionOpen_NeXus_file)
        self.menuFile.addAction(self.actionExport_to_NeXus_file)
        self.menuFile.addAction(self.actionExport_to_Filewriter_JSON)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "NeXus Constructor", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.componentsTab), QtWidgets.QApplication.translate("MainWindow", "Components", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.fileTab), QtWidgets.QApplication.translate("MainWindow", "NeXus File Layout", None, -1))
        self.menuFile.setTitle(QtWidgets.QApplication.translate("MainWindow", "File", None, -1))
        self.actionOpen_NeXus_file.setText(QtWidgets.QApplication.translate("MainWindow", "Open NeXus file", None, -1))
        self.actionExport_to_NeXus_file.setText(QtWidgets.QApplication.translate("MainWindow", "Export to NeXus file", None, -1))
        self.actionExport_to_Filewriter_JSON.setText(QtWidgets.QApplication.translate("MainWindow", "Export to Filewriter JSON", None, -1))

