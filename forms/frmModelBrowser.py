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
from UICore.mSqlite import Sqlite
import pandas as pd
import numpy as np

from UICore.histogram import ticks, best_bin, nice, kernelDensityEstimator, kde_bandwidth

Slot = pyqtSlot

test_pd = None

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
        self.splitter_preview.setSizes([500, self.splitter.width() - 490])
        self.resize(self.splitter_preview.width(), self.splitter_preview.height())
        self.splitter_preview.setupUi()

        self.tabWidget_model.setTabText(0, "预览图")
        self.tabWidget_model.setTabText(1, "模型信息")

        self.project = QgsProject()
        self.mapPreviewer.setProject(self.project)

        self.tree_model.setStyle(QStyleFactory.create("windows"))
        self.tree_model.currentItemChanged.connect(self.tree_model_currentItemChanged)

        self.chart_webView.loadFinished.connect(self.chart_webView_loadFinished)

        self.bFirst = True
        self.get_field_names()
        self.clear()

    def get_field_names(self):
        self.name_area = model_layer_meta.name_potentialLand_area.lower()
        self.name_type = model_layer_meta.name_type.lower()
        self.name_landid = model_layer_meta.name_landid.lower()
        self.name_unitid = model_layer_meta.name_unitid.lower()
        self.name_r_po = model_layer_meta.name_r_po.lower()
        self.name_CurBldAdj = model_layer_meta.name_CurBldAdj.lower()
        self.name_CurRBld = model_layer_meta.name_CurRBld.lower()
        self.name_MetroIf = model_layer_meta.name_MetroIF.lower()
        self.name_PublicService = model_layer_meta.name_PublicService.lower()
        self.name_layer_PotentialLand = model_layer_meta.name_layer_PotentialLand
        self.name_layer_match = model_layer_meta.name_layer_match
        self.name_potentialLand_area = model_layer_meta.name_potentialLand_area

    def updateForm(self, models=None):
        for model in models:
            if isinstance(model, ModelResult):
                layItem = QTreeWidgetItem([model.name])
                layItem.setIcon(0, QIcon(QPixmap(":/icons/icons/mGeoPackage.svg")))
                layItem.setData(0, Qt.UserRole, model)

                self.tree_model.addTopLevelItem(layItem)

                if self.bFirst:
                    self.tree_model.setCurrentItem(layItem)
                    self.bFirst = False

        if self.bFirst:
            self.tree_model.collapseAll()

    # 绘制直方图
    def draw_histogram(self, df):
        #  net increase
        # df_filter = (df[self.name_r_po] - df[self.name_CurRBld]).map(
        #     lambda x: 0 if x < 0 else x
        # )
        # df_filter = df_filter[df_filter > 0]

        #  demolish
        # df_filter = df[self.name_CurRBld]
        # df_filter = df_filter[df_filter > 0]

        #  acc

        #  pubervice
        df_filter = df[self.name_PublicService]

        transfer_hist, transfer_density, [start, stop, count] = self.hist_transfer_data(df_filter)

        jscode = "show_hist({}, {}, {});".format(transfer_hist, transfer_density, [start, stop, count])
        self.chart_webView.page().mainFrame().evaluateJavaScript(jscode)

    def hist_transfer_data(self, df):
        count = best_bin(df)
        # count = 8
        [start, stop] = nice(min(df), max(df), count)
        interval = ticks(start, stop, count)
        bandwidth = np.diff(interval)
        x0 = (interval[0] + interval[1]) / 2
        bandwidth = np.insert(bandwidth, 0, x0)
        x = np.cumsum(bandwidth)
        hist, bins = np.histogram(df, bins=interval, density=False)
        hist = hist / df.count()

        # kde_bw = kde_bandwidth(df_net)
        density, kde_bw = kernelDensityEstimator(df.tolist(), interval)
        # density = kernelDensityEstimator(df_net.tolist(), interval, False)
        density = list(map(lambda x: x * kde_bw, density))

        transfer_hist = [[x[i], hist[i]] for i in range(len(x) - 1)]
        transfer_density = [[x[i], density[i]] for i in range(len(x) - 1)]

        print(transfer_hist)

        return transfer_hist, transfer_density, [start, stop, count]

    #  绘制雷达图
    def draw_radar(self, model):
        ranges = model.ranges

        indicator = []
        values = []
        for k, v in ranges.items():
            dict = {
                'text': indicator_translate_dict[k],
                'max': round(v[1], 2),
                'min': round(v[0], 2)
            }
            values.append(round(v[2], 2))
            indicator.append(dict)

        jscode = "show_radar({}, {});".format(indicator, values)
        self.chart_webView.page().mainFrame().evaluateJavaScript(jscode)

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
            self.draw_radar(model)
            self.draw_histogram(test_pd)

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

    sqlite_db = Sqlite(r"D:\空间模拟\SpatialSimulation\tmp\2023-07-17-14-56-59.sqlite")
    exec_str = '''
        select * from 居住专规潜力用地_0621_s2 where io=1
    '''
    r = sqlite_db.execute_dict(exec_str)
    test_pd = pd.DataFrame.from_dict(r)

    window.updateForm([model_res1, model_res2])
    window.setWindowFlags(Qt.Window)
    window.show()
    sys.exit(app.exec_())