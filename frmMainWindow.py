import os
from os.path import basename

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QShowEvent, QPixmap
from PyQt5.QtWidgets import QApplication, QMessageBox, QMainWindow, QSystemTrayIcon, QAction, QMenu, QFileDialog
from PyQt5 import QtCore
from qgis._core import QgsProject, QgsLayerTreeModel, QgsVectorLayer
from qgis._gui import QgsLayerTreeMapCanvasBridge

import UI.UIMainWindow
import sys

from UICore.Gv import Window_titles, Tools
from forms import frmLogView, frmModelCal

from UICore.log4p import Log
from forms.frmIdentifyResult import frmIdentfiyResult
from widgets.mDock import mDock
from widgets.mapTool import mapTools
from osgeo import ogr

Slot = QtCore.pyqtSlot

log = Log(__name__)


class Ui_Window(QMainWindow, UI.UIMainWindow.Ui_MainWindow):
    def __init__(self):
        super(Ui_Window, self).__init__()

        self.setupUi(self)

        self.setWindowState(Qt.WindowMaximized)  # 窗口最大化
        # self.setFixedSize(QSize(800, 600))
        self.statusbar.setSizeGripEnabled(False)
        # self.setDockNestingEnabled(False)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)

        self.bFirstHint = True

        self.mapCanvas.setCanvasColor(Qt.white)
        self.mapCanvas.setVisible(True)
        self.mapCanvas.xyCoordinates.connect(self.showXY)
        # self.setCentralWidget(self.mapCanvas)

        # self.createMapTools()
        self.createActions()
        self.createMapTools()
        self.createMenus()
        self.createToolbars()
        self.createDockWindows()

        self.root = QgsProject.instance().layerTreeRoot()
        self.model = QgsLayerTreeModel(self.root,self)
        self.model.setFlag(QgsLayerTreeModel.AllowNodeReorder)
        self.model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility)
        self.tocView.setModel(self.model)

        self.bridge = QgsLayerTreeMapCanvasBridge(self.root, self.mapCanvas, self)

        # vlayout = QVBoxLayout(self)
        # vlayout.addWidget(self.splitter)
        # vlayout.setContentsMargins(0, 0, 10, 10)

        # self.splitter.setGeometry(0, 0, self.width(), self.height())
        # self.splitter.setOrientation(Qt.Horizontal)
        # self.splitter.setProperty("Stretch", SplitterState.collapsed)
        # self.splitter.setProperty("Dock", Dock.right)
        # self.splitter.setProperty("WidgetToHide", self.tabWidget)
        # self.splitter.setProperty("ExpandParentForm", True)

        # self.splitter.setSizes([700, self.splitter.width() - 690])
        # self.resize(self.splitter.width(), self.splitter.height())

        self.setCentralWidget(self.mapCanvas)  # 非常重要，否则splitter不会铺满窗口

        # self.splitter.splitterMoved.connect(self.splitterMoved)
        # self.splitter.handle(1).handleClicked.connect(self.handleClicked)

        # self.splitter.setupUi()

        self.createTrayIcon()
        self.trayIcon.activated.connect(self.iconActivated)
        self.trayIcon.show()

        # self.tabWidget.setTabsClosable(True)
        # self.tabWidget.tabCloseRequested.connect(lambda index: self.tabWidget.removeTab(index))
        # self.tabWidget.setCurrentWidget(self.tocView)

    def createActions(self):
        self.actionAddLayer = QAction("加载图层...", self, shortcut="Ctrl+A",
                                      triggered=self.addLayer)
        self.actionAddLayer.setIcon(QIcon(QPixmap(":/icons/icons/mActionDataSourceManager.svg")))

        self.actionOpen = QAction("打开优化传导模型...", self, shortcut="Ctrl+O",
                                  triggered=self.OpenParam)

        self.actionExit = QAction("退出", self, shortcut="Ctrl+Q",
                                  triggered=self.exit)

        self.actionAbout = QAction("关于", self, triggered=self.about)

        self.minimizeAction = QAction("隐藏", self, triggered=self.hide)
        self.restoreAction = QAction("还原", self, triggered=self.showNormal)
        self.quitAction = QAction("退出", self, triggered=QApplication.instance().quit)

        self.actionModelCal = QAction("新建优化传导模型", self)
        self.actionModelCal.setIcon(QIcon(":/icons/icons/度量地理分布.png"))
        self.actionModelCal.triggered.connect(self.openModelCal)

    def createMapTools(self):
        mt = mapTools(self.mapCanvas)
        self.actionZoomIn = mt.Create(Tools.zoomIn)
        self.actionZoomOut = mt.Create(Tools.zoomOut)
        self.actionPan = mt.Create(Tools.pan)
        self.actionIdentifyFeature = mt.Create(Tools.identifyFeature)

        # self.actionIdentifyFeature = QAction("要素查询", self)
        # self.actionIdentifyFeature.setEnabled(True)
        # self.actionIdentifyFeature.triggered.connect(self.act)
        #
        # self.IdentifyFeature = QgsMapToolIdentifyFeature(self.mapCanvas)
        # self.IdentifyFeature.featureIdentified.connect(self.showFeatures)
        # self.IdentifyFeature.setAction(self.actionIdentifyFeature)
        # self.mapCanvas.setMapTool(self.IdentifyFeature)

    # def act(self):
    #     self.mapCanvas.setMapTool(self.IdentifyFeature)
    #
    #     layers = self.mapCanvas.layers()
    #     if layers:
    #         self.IdentifyFeature.setLayer(layers[0])
    #         print("active")
    #     else:
    #         self.IdentifyFeature.setLayer(None)
    #         print("none")
    #
    # def showFeatures(self, feature):
    #     if feature is not None:
    #         log.info("You clicked on feature {}".format(feature.id()))

    def createMenus(self):
        self.fileMenu = QMenu("文件", self)
        self.fileMenu.addAction(self.actionAddLayer)
        self.fileMenu.addAction(self.actionExit)

        self.viewMenu = QMenu("视图", self)
        self.viewMenu.addAction(self.actionZoomIn)
        self.viewMenu.addAction(self.actionZoomOut)
        self.viewMenu.addAction(self.actionPan)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.actionIdentifyFeature)
        self.viewMenu.addSeparator()

        self.modelMenu = QMenu("模型", self)
        self.modelMenu.addAction(self.actionModelCal)
        self.modelMenu.addAction(self.actionOpen)

        self.helpMenu = QMenu("帮助", self)
        self.helpMenu.addAction(self.actionAbout)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.modelMenu)
        self.menuBar().addMenu(self.helpMenu)

    def createToolbars(self):
        self.mainToolbar.addAction(self.actionAddLayer)
        self.mainToolbar.addAction(self.actionModelCal)
        self.mainToolbar.addSeparator()
        self.mainToolbar.addAction(self.actionPan)
        self.mainToolbar.addAction(self.actionZoomIn)
        self.mainToolbar.addAction(self.actionZoomOut)
        self.mainToolbar.addSeparator()
        self.mainToolbar.addAction(self.actionIdentifyFeature)

    def createDockWindows(self):
        self.dockLayer = mDock(Window_titles.layer, self)
        self.dockLayer.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        # self.dockLayer.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dockLayer.setWidget(self.tocView)
        # dock.topLevelChanged.connect(self.dockSetWinFlags)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockLayer)
        self.viewMenu.addAction(self.dockLayer.toggleViewAction())

        self.dockModelCal = mDock(Window_titles.model, self)
        self.dockModelCal.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        widgetModalCal = frmModelCal.frmModelCal(self)
        self.dockModelCal.setWidget(widgetModalCal)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockModelCal)

        self.dockLogView = mDock(Window_titles.logView, self)
        self.dockLogView.setAllowedAreas(Qt.AllDockWidgetAreas)
        widgetLogView = frmLogView.frmLogView(parent=self)
        self.dockLogView.setWidget(widgetLogView)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dockLogView)
        self.viewMenu.addAction(self.dockLogView.toggleViewAction())

        self.dockIdentifyResult = frmIdentfiyResult(self)

        # self.tabifyDockWidget(self.dockModelCal, self.dockLayer)
        self.dockModelCal.close()
        self.dockLogView.close()
        # self.dockIdentifyResult.hide()

    def addLayer(self):
        # path_to_vec = QFileDialog.getOpenFileName()[0]

        path_to_vec = QFileDialog.getOpenFileName(
            self, "选择待转换矢量图层文件", os.getcwd(),
            "ESRI Shapefile(*.shp)")[0]

        if path_to_vec == "":
            return

        layer = QgsVectorLayer(path_to_vec, basename(path_to_vec))
        if not layer.isValid():
            QMessageBox.information(self, '提示', '文件打开失败', QMessageBox.Ok)
            return

        QgsProject.instance().addMapLayers([layer])
        self.mapCanvas.setLayers([layer])
        self.mapCanvas.setExtent(layer.extent())
        self.mapCanvas.refresh()

        self.actionIdentifyFeature.identifyFeature([layer])

    def exit(self):
        QMessageBox.information(self, "提示", "退出", QMessageBox.Close)

    def OpenParam(self):
        QMessageBox.information(self, "提示", "打开模型参数文件", QMessageBox.Close)

    def about(self):
        QMessageBox.information(self, "提示", "关于", QMessageBox.Close)

    def openModelCal(self):
        self.viewMenu.addAction(self.dockModelCal.toggleViewAction())
        self.dockModelCal.show()

    def showXY(self,point):
        self.statusBar().showMessage("坐标: {}, {}".format(str(point.x()), str(point.y())))

    def showEvent(self, a0: QShowEvent) -> None:
        desktop = QApplication.desktop()
        self.move(int((desktop.width() - self.width())/2), int((desktop.height() - self.height())/2))

    @Slot(QSystemTrayIcon.ActivationReason)
    def iconActivated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.showNormal()

    def createTrayIcon(self):
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QIcon(":/icons/icons/地理学院.png"))

        self.trayIcon.setToolTip(self.windowTitle())

    def closeEvent(self, event):
        if self.bFirstHint:
            QMessageBox.information(self, "工具集",
                                    "窗口将缩至系统托盘并在后台继续运行,如需完全"
                                    "退出程序请在托盘小图标的右键菜单中选择<b>退出</b>按钮.")
            self.bFirstHint = False

        self.hide()
        event.ignore()


if __name__ == '__main__':
    ogr.UseExceptions()
    app = QApplication(sys.argv)
    # Enable high DPI scaling
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    # style = QStyleFactory.create("windows")
    # app.setStyle(style)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "工具集", "无法检查到系统托盘程序.")
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    frmMain = Ui_Window()
    frmMain.show()

    sys.exit(app.exec_())
