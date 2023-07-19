import os
from random import randint

from PyQt5.QtCore import Qt, QSize, pyqtSlot, QUrl, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWidgets import QMainWindow, QApplication, QStyleFactory, QTreeWidgetItem, QMessageBox
import sys

from qgis._core import QgsVectorLayer, QgsProject, QgsApplication

from UI.UIModelBrowser import Ui_ModelBrowser
from UICore.Gv import SplitterState, Dock, model_layer_meta, model_config_params, indicator_translate_dict, \
    get_main_path
from UICore.SCIPCal import ModelResult
import icons_rc

Slot = pyqtSlot

class UI_ModelBrowser(QMainWindow, Ui_ModelBrowser):
    def __init__(self, parent=None):
        super(UI_ModelBrowser, self).__init__(parent=parent)
        self.parent = parent
        self.setupUi(self)

        self.setWindowTitle("模型结果管理器")
        self.setWindowState(Qt.WindowMaximized)  # 窗口最大化

        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setProperty("Stretch", SplitterState.expanded)
        self.splitter.setProperty("Dock", Dock.left)
        self.splitter.setProperty("WidgetToHide", self.tree_model)
        self.splitter.setProperty("ExpandParentForm", False)
        self.splitter.setSizes([150, self.splitter.width() - 140])
        self.resize(self.splitter.width(), self.splitter.height())
        self.splitter.setupUi()

        self.setCentralWidget(self.splitter)

        self.splitter_preview.setOrientation(Qt.Horizontal)
        self.splitter_preview.setProperty("Stretch", SplitterState.expanded)
        self.splitter_preview.setProperty("Dock", Dock.right)
        self.splitter_preview.setProperty("WidgetToHide", self.chart_webView)
        self.splitter_preview.setProperty("ExpandParentForm", False)
        self.splitter_preview.setSizes([600, self.splitter.width() - 590])
        self.resize(self.splitter_preview.width(), self.splitter_preview.height())
        self.splitter_preview.setupUi()

        self.tabWidget_model.setTabText(0, "预览图")
        self.tabWidget_model.setTabText(1, "模型信息")

        self.project = QgsProject()
        self.mapPreviewer.setProject(self.project)

        self.tree_model.setStyle(QStyleFactory.create("windows"))
        self.tree_model.currentItemChanged.connect(self.tree_model_currentItemChanged)

        self.chart_webView.loadFinished.connect(self.chart_webView_loadFinished)

        self.clear()

    def updateForm(self, models=None):
        bFirst = True
        for model in models:
            if isinstance(model, ModelResult):
                layItem = QTreeWidgetItem([model.name])
                layItem.setIcon(0, QIcon(QPixmap(":/icons/icons/mGeoPackage.svg")))
                layItem.setData(0, Qt.UserRole, model)

                self.tree_model.addTopLevelItem(layItem)

                if bFirst:
                    self.tree_model.setCurrentItem(layItem)
                    bFirst = False

        self.tree_model.collapseAll()

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def tree_model_currentItemChanged(self, cur_item: QTreeWidgetItem, previous_item: QTreeWidgetItem):
        print("Changed")

        model = cur_item.data(0, Qt.UserRole)

        if model is not None:
            self.current_model = model
        else:
            return

        lyrs = []
        for v in model.layers.values():
            lyr = QgsVectorLayer("{}|layername={}".format(model.dataSource,
                                                          model.layers["{}".format(v)]), v, 'ogr')

            if not lyr.isValid():
                QMessageBox.information(self, '提示', '文件打开失败', QMessageBox.Ok)
                return

            self.mapPreviewer.setExtent(lyr.extent())
            lyrs.append(lyr)

        self.project.addMapLayers(lyrs)
        self.mapPreviewer.setLayers(lyrs)
        self.mapPreviewer.refresh()

        # chart_path = os.path.join(get_main_path(), "resources", "radar_hist.html")
        # self.chart_webView.load(QUrl.fromLocalFile(os.path.abspath(chart_path)))
        self.chart_webView.load(QUrl.fromLocalFile(os.path.abspath(r'../resources/radar_hist.html')))

    @Slot(bool)
    def chart_webView_loadFinished(self, bflag: bool):
        if bflag:
            model = self.current_model
            ranges = model.ranges

            indicator = []
            values = []
            for k, v in ranges.items():
                dict = {}
                dict['text'] = indicator_translate_dict[k]

                dict['max'] = round(v[1], 2)
                dict['min'] = round(v[0], 2)
                values.append(round(v[2], 2))
                indicator.append(dict)

            print(str(indicator))

            jscode = "showChart({}, {});".format(indicator, values)
            self.chart_webView.page().mainFrame().evaluateJavaScript(jscode)

    def clear(self):
        self.tree_model.clear()
        self.tree_model.setColumnCount(1)
        self.tree_model.headerItem().setText(0, "模型列表")
        # self.tree_model.setHeader()
        # self.tree_model.setHeaderHidden(True)
        self.tree_model.sortByColumn(-1, Qt.AscendingOrder)

if __name__ == '__main__':
    # app = QApplication(sys.argv)
    app = QgsApplication([], True)

    window = UI_ModelBrowser()
    model_res1 = ModelResult()
    model_res1.name = 'model_2023-07-17-20-07-38'
    model_res1.dataSource = r'D:\空间模拟\SpatialSimulation\res\model_files\model_2023-07-17-20-07-38.sqlite'
    model_res1.layers = {'居住专规潜力用地_0621_s2': '居住专规潜力用地_0621_s2', '标准单元_0621_s2': '标准单元_0621_s2'}
    model_res1.ranges = {'Total net increase R building': [0, 4925353.334999999, 2348936.6530000074], 'Total demolish building area': [-18825600.5823172, 0, -2949169.581999993], 'Total Metro cover buidling area': [0, 10739080.282, 1493.8861800817494], 'Total cover public service area': [0, 3896.1128, 1789.9464999999973], 'BI': [0, 6.633899399999999, 0.7677029]}

    model_res2 = ModelResult()
    model_res2.name = '2023-07-17-20-42-03'
    model_res2.dataSource = r'D:\空间模拟\SpatialSimulation\res\model_files\model_2023-07-17-20-07-38.sqlite'
    model_res2.layers = {'居住专规潜力用地_0621_s2': '居住专规潜力用地_0621_s2', '标准单元_0621_s2': '标准单元_0621_s2'}
    model_res2.ranges = {'Total net increase R building': [0, 4925353.334999999, 2348936.6530000074], 'Total demolish building area': [-18825600.5823172, 0, -2949169.581999993], 'Total Metro cover buidling area': [0, 10739080.282, 1493.8861800817494], 'Total cover public service area': [0, 3896.1128, 1789.9464999999973], 'BI': [0, 6.633899399999999, 0.7677029]}

    window.updateForm([model_res1, model_res2])
    window.setWindowFlags(Qt.Window)
    window.show()
    sys.exit(app.exec_())
