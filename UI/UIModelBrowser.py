# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UIModelBrowser.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ModelBrowser(object):
    def setupUi(self, ModelBrowser):
        ModelBrowser.setObjectName("ModelBrowser")
        ModelBrowser.resize(1084, 683)
        self.centralwidget = QtWidgets.QWidget(ModelBrowser)
        self.centralwidget.setObjectName("centralwidget")
        self.splitter = CollapsibleSplitter(self.centralwidget)
        self.splitter.setGeometry(QtCore.QRect(150, 100, 811, 441))
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.tree_model = QtWidgets.QTreeWidget(self.splitter)
        self.tree_model.setObjectName("tree_model")
        self.tree_model.headerItem().setText(0, "1")
        self.tabWidget_model = QtWidgets.QTabWidget(self.splitter)
        self.tabWidget_model.setObjectName("tabWidget_model")
        self.tab_previewer = QtWidgets.QWidget()
        self.tab_previewer.setObjectName("tab_previewer")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.tab_previewer)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter_preview = CollapsibleSplitter(self.tab_previewer)
        self.splitter_preview.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_preview.setObjectName("splitter_preview")
        self.mapPreviewer = QgsMapCanvas(self.splitter_preview)
        self.mapPreviewer.setObjectName("mapPreviewer")
        self.chart_webView = QtWebKitWidgets.QWebView(self.splitter_preview)
        self.chart_webView.setObjectName("chart_webView")
        self.horizontalLayout.addWidget(self.splitter_preview)
        self.tabWidget_model.addTab(self.tab_previewer, "")
        self.tab_info = QtWidgets.QWidget()
        self.tab_info.setObjectName("tab_info")
        self.tabWidget_model.addTab(self.tab_info, "")
        ModelBrowser.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(ModelBrowser)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1084, 23))
        self.menubar.setObjectName("menubar")
        ModelBrowser.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(ModelBrowser)
        self.statusbar.setObjectName("statusbar")
        ModelBrowser.setStatusBar(self.statusbar)

        self.retranslateUi(ModelBrowser)
        self.tabWidget_model.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(ModelBrowser)

    def retranslateUi(self, ModelBrowser):
        _translate = QtCore.QCoreApplication.translate
        ModelBrowser.setWindowTitle(_translate("ModelBrowser", "模型结果管理器"))
        self.tabWidget_model.setTabText(self.tabWidget_model.indexOf(self.tab_previewer), _translate("ModelBrowser", "Tab 1"))
        self.tabWidget_model.setTabText(self.tabWidget_model.indexOf(self.tab_info), _translate("ModelBrowser", "Tab 2"))
from PyQt5 import QtWebKitWidgets
from qgis.gui import QgsMapCanvas
from widgets.CollapsibleSplitter import CollapsibleSplitter
