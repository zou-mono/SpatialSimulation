import json
import os
import uuid

from PyQt5.QtCore import Qt, QSize, pyqtSlot, QUrl, QTimer, QItemSelection, QModelIndex, QItemSelectionModel, QPoint, \
    QPointF
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont, QTextDocument
from PyQt5.QtWidgets import QMainWindow, QStyleFactory, QTreeWidgetItem, QMessageBox, QMenu, QAction, QHBoxLayout,\
    QAbstractItemView
import sys

from qgis._core import QgsVectorLayer, QgsProject, QgsApplication, QgsSymbol, QgsSimpleFillSymbolLayer, \
    QgsMapLayerModel, QgsLayerTreeModel, QgsLayerTree, QgsLayerTreeGroup, QgsLayerTreeNode, QgsTextAnnotation, \
    QgsCoordinateReferenceSystem, QgsAnnotationPointTextItem, QgsAnnotationLayer, QgsMapLayer, QgsTextFormat
from qgis._gui import QgsFeatureListModel, QgsLayerTreeView, QgsLayerTreeMapCanvasBridge, QgsMapCanvasAnnotationItem

from UI.UIModelBrowser import Ui_ModelBrowser
from UICore.Gv import SplitterState, Dock, model_layer_meta, model_config_params, indicator_translate_dict, \
    get_main_path, modelRole, Window_titles, Tools, toc_groups
from UICore.SCIPCal import ModelResult
import icons_rc
from UICore.common import get_field_index_no_case, get_qgis_style
from UICore.log4p import Log
from UICore.mSqlite import Sqlite
import pandas as pd
import numpy as np

from UICore.histogram import ticks, best_bin, nice, kernelDensityEstimator
from UICore.renderer import categrorized_renderer, single_renderer
from forms.frmIdentifyResult import frmIdentfiyResult
from widgets.CollapsibleSplitter import CollapsibleSplitter
from widgets.mDock import mDock
from widgets.mapTool import mapTools
from UICore.Gv import model_config_params as g_cp, model_layer_meta as g_lm

Slot = pyqtSlot

log = Log(__name__)

test_land = None
test_grid = None

class UI_ModelBrowser(QMainWindow, Ui_ModelBrowser):
    def __init__(self, parent=None, chart_path=""):
        super(UI_ModelBrowser, self).__init__(parent=parent)
        self.parent = parent
        self.setupUi(self)

        self.setWindowTitle("模型结果管理器")
        self.setWindowState(Qt.WindowMaximized)  # 窗口最大化

        self.splitter.resize(self.width(), self.height())
        self.setCentralWidget(self.splitter)

        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setProperty("Stretch", SplitterState.expanded)
        self.splitter.setProperty("Dock", Dock.left)
        self.splitter.setProperty("WidgetToHide", self.tree_model)
        self.splitter.setProperty("ExpandParentForm", False)
        self.splitter.setSizes([int(self.splitter.width() * 0.2), int(self.splitter.width() * 0.8 - 10)])
        # self.resize(self.splitter.width(), self.splitter.height())
        self.splitter.setupUi()

        self.splitter_preview.setOrientation(Qt.Horizontal)
        self.splitter_preview.setProperty("Stretch", SplitterState.expanded)
        self.splitter_preview.setProperty("Dock", Dock.right)
        self.splitter_preview.setProperty("WidgetToHide", self.chart_webView)
        self.splitter_preview.setProperty("ExpandParentForm", False)
        self.splitter_preview.setSizes([int(self.splitter.width() * 0.5), int(self.splitter.width() * 0.3 - 10)])
        # self.resize(self.splitter_preview.width(), self.splitter_preview.height())
        self.splitter_preview.setupUi()

        self.splitter_toc.setOrientation(Qt.Vertical)
        self.splitter_toc.setProperty("Stretch", SplitterState.expanded)
        self.splitter_toc.setProperty("Dock", Dock.down)
        self.splitter_toc.setProperty("WidgetToHide", self.tocView)
        self.splitter_toc.setProperty("ExpandParentForm", False)
        self.splitter_toc.setSizes([int(self.splitter.height() * 0.5), int(self.splitter.height() * 0.5 - 10)])
        self.splitter_toc.setupUi()

        self.tabWidget_model.setTabText(0, "预览图")
        self.tabWidget_model.setTabText(1, "模型信息")

        self.chart_webView.loadFinished.connect(self.chart_webView_loadFinished)

        self.createActions()
        self.createMapTools()
        self.createMenus()
        self.createToolbars()
        self.createDockWindows()

        self.project = QgsProject()
        self.mapPreviewer.setProject(self.project)
        self.root = self.project.layerTreeRoot()
        self.model = QgsLayerTreeModel(self.root, self)
        self.model.setFlag(QgsLayerTreeModel.AllowNodeReorder)
        # self.model.setFlag(QgsLayerTreeModel.ShowLegendAsTree)
        self.model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility)
        self.model.setFlag(QgsLayerTreeModel.UseTextFormatting)
        # self.model.setFlag(QgsLayerTreeModel.AllowLegendChangeState)
        self.tocView.setModel(self.model)
        self.bridge = QgsLayerTreeMapCanvasBridge(self.root, self.mapPreviewer, self)

        # self.tocView.viewOptions().showDecorationSelected = True
        # self.tocView.selectionModel().dataChanged.connect(self.toc_selectionChanged)
        # self.model.dataChanged.connect(self.toc_dataChanged)
        self.root.visibilityChanged.connect(self.checkChanged)
        self.tocView.setDragEnabled(False)

        self.tree_model.layer_added.connect(self.on_layer_added)

        # self.setStyle(QStyleFactory.create("fusion"))
        # self.tree_model.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # self.tree_model.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.tree_model.setMapModel(self.bridge)  # 将tree_model关联的信息传入
        self.bFirst = True
        self.get_field_names()
        self.clear()

        self.chart_path = chart_path
        self.init_tocView()

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
        self.name_plabi = model_layer_meta.name_plabi.lower()

    def createDockWindows(self):
        self.dockIdentifyResult = frmIdentfiyResult(self, Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)

    def createToolbars(self):
        pass

    def createActions(self):
        self.actionOpen = QAction("打开优化传导模型...", self, shortcut="Ctrl+O",
                                  triggered=self.OpenModels)

        self.actionExit = QAction("退出", self, shortcut="Ctrl+Q",
                                  triggered=self.exit)

    def createMenus(self):
        self.modelMenu = QMenu("模型", self)
        self.modelMenu.addAction(self.actionOpen)
        self.modelMenu.addSeparator()
        self.modelMenu.addAction(self.actionExit)

        self.viewMenu = QMenu("视图", self)
        self.viewMenu.addAction(self.actionZoomIn)
        self.viewMenu.addAction(self.actionZoomOut)
        self.viewMenu.addAction(self.actionPan)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.actionIdentifyFeature)
        actionTocview = QTocView(self, self.mapPreviewer, self.splitter_toc)
        self.viewMenu.addAction(actionTocview)

        self.menuBar().addMenu(self.modelMenu)
        self.menuBar().addMenu(self.viewMenu)

    def createMapTools(self):
        mt = mapTools(self.mapPreviewer)
        self.actionZoomIn = mt.Create(Tools.zoomIn)
        self.actionZoomOut = mt.Create(Tools.zoomOut)
        self.actionPan = mt.Create(Tools.pan)
        self.actionIdentifyFeature = mt.Create(Tools.identifyFeature)

    def OpenModels(self):
        pass

    def exit(self):
        self.close()

    def updateForm(self, models=None):
        for model in models:
            if isinstance(model, ModelResult):
                layItem = QTreeWidgetItem([model.name])
                layItem.setIcon(0, QIcon(QPixmap(":/icons/icons/mGeoPackage.svg")))
                layItem.setData(0, modelRole.model, model)
                # layItem.setData(0, modelRole.modelID, model.ID)

                self.tree_model.addTopLevelItem(layItem)

                if self.bFirst:
                    self.tree_model.setCurrentItem(layItem)
                    self.bFirst = False

                for sol_key, sol_v in model.score.items():
                    if sol_key == model_config_params.Indicator_multi:
                        sol_name = "多目标最优方案"
                    else:
                        sol_name = "单目标:" + indicator_translate_dict[sol_key] + "最优方案"

                    child = QTreeWidgetItem([sol_name])
                    child.setIcon(0, QIcon(QPixmap(":/icons/icons/优化方案.svg")))
                    child.setData(0, modelRole.model, model)
                    child.setData(0, modelRole.solution, {
                        'name': sol_name,
                        'key': sol_key
                    })
                    layItem.addChild(child)

                # for k, v in model.layers.items():
                #     lyr = QgsVectorLayer("{}|layername={}".format(model.dataSource, v) , v, 'ogr')
                #
                #     child = QTreeWidgetItem([v])
                #     child.setData(0, QgsMapLayerModel.LayerRole, lyr)
                #     child.setData(0, modelRole.model, model)
                #     layItem.addChild(child)
                #
                #     if not lyr.isValid():
                #         log.warning("图层文件{}读取失败".format("{}|layername={}".format(model.dataSource, v)))
                #         return

        if self.bFirst:
            self.tree_model.expandAll()

    #  初始化tocView，增加固定的group
    def init_tocView(self):
        for v in toc_groups.values():
            self.root.addGroup(v[0])

        groups = self.root.findGroups()
        for group in groups:
            group.setItemVisibilityCheckedRecursive(False)

            # group.setDragEnabled(False)

    # def toc_dataChanged(self, topleft: QModelIndex, bottomright: QModelIndex, roles):
    #     print("selected")

    #  控制tocView上图层和group的开关事件
    #  group设计为单选，排他性
    def checkChanged(self, node: QgsLayerTreeNode):
        groups = self.root.findGroups()

        # print(node.name() + "_" + str(node.nodeType()))

        if node.nodeType() == 0:
            if node.isVisible():
                for group in groups:
                    if group != node:
                        group.setItemVisibilityCheckedRecursive(False)
                    else:
                        group.setItemVisibilityCheckedRecursive(True)
            else:
                node.setItemVisibilityCheckedRecursive(False)

    # 图层加载完成后绘制相应的chart，增加相应的装饰文字
    def on_layer_added(self, items: list):
        if items is None:
            return
        if len(items) < 1:
            return

        top_item = items[len(items) - 1]
        self.add_model_decoration_text(top_item)

        # model = top_item.data(0, modelRole.model)
        # cur_solution_name = top_item.data(0, modelRole.solution)['name']
        # print(model.name + "_" + cur_solution_name)

        # self.add_annonation_text(top_item)

        self.load_items = items

        if self.chart_path == "":
            self.chart_path = os.path.join(get_main_path(), "resources", "radar_hist.html")
        self.chart_webView.load(QUrl.fromLocalFile(os.path.abspath(self.chart_path)))

    def add_model_decoration_text(self, cur_item):
        model_name = cur_item.data(0, modelRole.model).name
        solution_name = cur_item.data(0, modelRole.solution)['name']
        self.txt_model.setText(model_name)
        self.txt_solution.setText(solution_name)

    def add_annonation_text(self, top_item):
        model = top_item.data(0, modelRole.model)
        cur_solution_name = top_item.data(0, modelRole.solution)['name']

        text = '''
            模型名称：{}
            方案名称：{}
        '''.format(model.name, cur_solution_name)

        notelayer = QgsAnnotationLayer('文字注记', QgsAnnotationLayer.LayerOptions(self.project.transformContext()))
        map_coord = self.mapPreviewer.getCoordinateTransform().toMapCoordinates(QPoint(0, 0))
        a_layer = QgsAnnotationPointTextItem(text, map_coord)
        a_layer.setAlignment(alignment=Qt.AlignLeft)
        text_format = QgsTextFormat()
        text_format.setFont(QFont("微软雅黑"))
        text_format.setSize(20)
        a_layer.setFormat(text_format)
        notelayer.addItem(a_layer)
        # notelayer.setFlags(QgsMapLayer.Private)  # 不允许annnotationlayer显示在tocView
        self.project.addMapLayer(notelayer)
        # self.project.annotationManager().addAnnotation(a)

    # 绘制直方图
    def draw_histogram(self, items):
        transfer_dict = {}

        for cur_item in items:
            model = cur_item.data(0, modelRole.model)
            cur_solution = cur_item.data(0, modelRole.solution)['key']
            cur_solution_name = cur_item.data(0, modelRole.solution)['name']

            indicator_dict = {}

            sqlite_db = Sqlite(model.dataSource)
            exec_str = '''
                select * from {} where {}=1
            '''.format(model.layers[cur_solution]['land'], model_layer_meta.name_io)
            df_land = pd.DataFrame.from_dict(sqlite_db.execute_dict(exec_str))

            exec_str = '''
                select {} from {}
            '''.format(model_layer_meta.name_plabi, model.layers[cur_solution]['grid'])
            df_grid = pd.DataFrame.from_dict(sqlite_db.execute_dict(exec_str))

            if len(df_land) ==0 or len(df_grid) == 0:
                log.warning("优化结果图层读取为空，无法进行直方图展示.")
                return

            # net increase
            df_filter = (df_land[self.name_r_po] - df_land[self.name_CurRBld]).map(
                lambda x: 0 if x < 0 else x
            )
            df_filter = df_filter[df_filter > 0]
            indicator_dict = self.transfer_to_dict(indicator_dict, df_filter, model_config_params.Indicator_net)

            # demolish
            df_filter = df_land[self.name_CurRBld]
            df_filter = df_filter[df_filter > 0]
            indicator_dict = self.transfer_to_dict(indicator_dict, df_filter, model_config_params.Indicator_demo)

            # acc
            df_filter = df_land.query('{}==1'.format(self.name_MetroIf))[
                "{}".format(self.name_r_po)]
            df_filter = df_filter[df_filter > 0]
            indicator_dict = self.transfer_to_dict(indicator_dict, df_filter, model_config_params.Indicator_acc)

            #  pubervice
            df_filter = df_land[self.name_PublicService]
            df_filter = df_filter[df_filter > 0]
            indicator_dict = self.transfer_to_dict(indicator_dict, df_filter, model_config_params.Indicator_pubService)

            #  BI
            df_filter = df_grid[self.name_plabi]
            df_filter = df_filter[df_filter > 0]
            indicator_dict = self.transfer_to_dict(indicator_dict, df_filter, model_config_params.Indicator_bi)

            if model.name not in transfer_dict:
                transfer_dict[model.name] = {}
            transfer_dict[model.name][cur_solution] = {
                'sol_name': cur_solution_name,
                'indicator': indicator_dict
            }

        transfer_data = json.dumps(transfer_dict, ensure_ascii=False)
        jscode = "get_hist_data('{}');".format(transfer_data)
        self.chart_webView.page().mainFrame().evaluateJavaScript(jscode)

    def transfer_to_dict(self, transfer_dict, df_filter, key_):
        transfer_hist, transfer_density, [start, stop, count] = self.hist_transfer_data(df_filter)
        transfer_dict[key_] = {
            "indicator_name": indicator_translate_dict[key_],
            "hist": transfer_hist,
            "density": transfer_density,
            "range": [start, stop, count]
        }
        return transfer_dict

    def hist_transfer_data(self, df):
        count = best_bin(df)
        if count < 10: count = 10
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
        transfer_density = [[interval[i], density[i]] for i in range(len(interval) - 1)]

        return transfer_hist, transfer_density, [start, stop, count]

    #  绘制雷达图
    def draw_radar(self, items):
        values = []
        indicator = []
        indicator_merge_range = {}

        bFirst = True
        for cur_item in items:
            model = cur_item.data(0, modelRole.model)
            cur_solution = cur_item.data(0, modelRole.solution)['key']
            cur_solution_name = cur_item.data(0, modelRole.solution)['name']
            node_name = model.name + "_" + cur_solution_name

            scores = model.score
            ranges = model.ranges

            if bFirst:
                bFirst = False
                for k, v in ranges.items():
                    indicator_merge_range[k] = {
                        'max': v[1],
                        'min': v[0]
                    }
            else:
                for k, v in ranges.items():
                    indicator_merge_range[k]['min'] = min(indicator_merge_range[k]['min'], v[0])
                    indicator_merge_range[k]['max'] = max(indicator_merge_range[k]['max'], v[1])

            score = scores[cur_solution]
            values.append({
                'value': list(score['current'].values()),
                'name': node_name,
                'overall': score['overall']
            })

        for k, v in indicator_translate_dict.items():
            indicator.append({
                'text': v,
                'max': indicator_merge_range[k]['max'],
                'min': indicator_merge_range[k]['min']
            })


        jscode = "show_radar({}, {});".format(indicator, values)
        self.chart_webView.page().mainFrame().evaluateJavaScript(jscode)

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def tree_model_currentItemChanged(self, cur_item: QTreeWidgetItem, previous_item: QTreeWidgetItem):
        pass

    @Slot(QItemSelection, QItemSelection)
    def tree_model_selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        if selected.isEmpty():
            return

        selected_count = len(self.tree_model.selectionModel().selectedIndexes())

        if selected_count > 1:
            # 多选情况下，只要已选中的节点中包括父节点，就不允许选中
            for cur in selected.indexes():
                if cur.parent().data() is None:
                    self.tree_model.selectionModel().select(cur, QItemSelectionModel.Deselect)

    @Slot(bool)
    def chart_webView_loadFinished(self, bflag: bool):
        if self.load_items is None:
            return

        if bflag:
            self.draw_radar(self.load_items)
            self.draw_histogram(self.load_items)

    def clear(self):
        self.tree_model.clear()
        self.tree_model.setColumnCount(1)
        self.tree_model.headerItem().setText(0, "模型列表")
        # self.tree_model.setHeader()
        # self.tree_model.setHeaderHidden(True)
        self.tree_model.sortByColumn(-1, Qt.AscendingOrder)


def topmostItem(item):
    while item.parent():
        item = item.parent()
    return item


class QTocView(QAction):
    def __init__(self, parent, mapCanvas, splitter: CollapsibleSplitter):
        super(QTocView, self).__init__("图层列表", parent)
        self.mapCanvas = mapCanvas
        self.setIconText("图层列表")
        self.setToolTip("图层列表")
        self.setEnabled(True)
        self.splitter = splitter
        self.setCheckable(True)
        self.toggled.connect(self.toggleState)

        if self.splitter.splitterState == SplitterState.expanded:
            self.setChecked(True)
        else:
            self.setChecked(False)

    def toggleState(self, checked):
        if checked:
            self.splitter.handleSplitterButton(SplitterState=SplitterState.collapsed)
        else:
            self.splitter.handleSplitterButton(SplitterState=SplitterState.expanded)


if __name__ == '__main__':
    # app = QApplication(sys.argv)
    QgsApplication.setPrefixPath('', True)
    app = QgsApplication([], True)
    cur_path, filename = os.path.split(os.path.abspath("./"))
    app.setPkgDataPath(os.path.abspath(cur_path))

    # app.setUITheme('Blend of Gray')
    QgsApplication.setUITheme('default')
    log.debug(app.uiThemes())
    # style = QStyleFactory.create("fusion")
    style = QStyleFactory.create("fusion")
    app.setStyle(style)
    # app.setStyle('Fusion')

    window = UI_ModelBrowser(chart_path=os.path.abspath(r'../resources/radar_hist.html'))

    model_res1 = ModelResult()
    model_res1.ID = str(uuid.uuid1())
    model_res1.name = 'model_2023-07-31-16-08-05'
    model_res1.dataSource = r'D:\空间模拟\SpatialSimulation\res\model_files\model_2023-08-04-16-39-36.sqlite'
    model_res1.layers = {'land': '居住专规潜力用地', 'grid': '标准单元',
                         'multiple': {'land': 'multiple_land', 'grid': 'multiple_grid'},
                         'NetIncRPo': {'land': 'NetIncRPo_land', 'grid': 'NetIncRPo_grid'},
                         'DemoBld': {'land': 'DemoBld_land', 'grid': 'DemoBld_grid'},
                         'Acc': {'land': 'Acc_land', 'grid': 'Acc_grid'},
                         'PublicService': {'land': 'PublicService_land', 'grid': 'PublicService_grid'}}
    model_res1.ranges = {'NetIncRPo': [0, 34885748.643418014], 'DemoBld': [-54045505.95386531, 0],
                         'Acc': [0, 35090984.655], 'PublicService': [0, 16760.1601], 'BI': [0, 21.62210046]}
    model_res1.score = {
        'multiple': {
            'current': {'NetIncRPo': 15364225.354680039, 'DemoBld': -15317557.4342225, 'Acc': 24312160.185000002,
                    'PublicService': 11867.470599999995, 'BI': 2.6562270999999997}, 'overall': 53.62},
        'NetIncRPo': {
            'current': {'NetIncRPo': 18535284.13230504, 'DemoBld': -12161314.008775942, 'Acc': 24401861.816999998,
                    'PublicService': 3908.6966999999995, 'BI': 2.7468455999999994}, 'overall': 47.24},
        'DemoBld': {
            'current': {'NetIncRPo': 16300817.014947858, 'DemoBld': -9662249.73705215, 'Acc': 22585008.737999998,
                    'PublicService': 3347.8207000000025, 'BI': 2.1058622}, 'overall': 44.58},
        'Acc': {
            'current': {'NetIncRPo': 16300817.014947856, 'DemoBld': -9662249.737052146, 'Acc': 22585008.737999998,
                    'PublicService': 3347.8207000000025, 'BI': 2.1058622}, 'overall': 44.58},
        'PublicService': {
            'current': {'NetIncRPo': 11126297.929674478, 'DemoBld': -17895987.479153745, 'Acc': 23763248.848,
                    'PublicService': 12822.730500000043, 'BI': 2.3017411}, 'overall': 50.73}}

    model_res2 = ModelResult()
    model_res2.ID = str(uuid.uuid1())
    model_res2.name = 'model_2023-08-04-19-53-49'
    model_res2.dataSource = r'D:\空间模拟\SpatialSimulation\res\model_files\model_2023-08-04-19-53-49.sqlite'
    model_res2.layers = {'land': '居住专规潜力用地',
                         'grid': '标准单元',
                         'multiple':
                             {'land': 'multiple_land',
                              'grid': 'multiple_grid'},
                         'NetIncRPo': {'land': 'NetIncRPo_land',
                                       'grid': 'NetIncRPo_grid'},
                         'PublicService': {'land': 'PublicService_land',
                                           'grid': 'PublicService_grid'}}
    model_res2.ranges = {'NetIncRPo': [0, 69771497.28683603],
                         'DemoBld': [-108091011.90773061, 0],
                         'Acc': [0, 70181969.31],
                         'PublicService': [0, 33520.3202],
                         'BI': [0, 41.58697848]}
    model_res2.score = {'multiple':
                            {'current':
                                 {'NetIncRPo': 50218241.39201991,
                                  'DemoBld': -69489710.18416594,
                                  'Acc': 59413208.53,
                                  'PublicService': 28643.168699999995,
                                  'BI': 22.621105120000003},
                             'overall': 66.44},
                        'NetIncRPo':
                            {'current':
                                 {'NetIncRPo': 53421098.246358156,
                                  'DemoBld': -66206336.222641245,
                                  'Acc': 59492920.448,
                                  'PublicService': 20621.439300000002,
                                  'BI': 22.711723620000004},
                             'overall': 63.24},
                        'PublicService':
                            {'current':
                                 {'NetIncRPo': 46000465.9930925,
                                  'DemoBld': -72029567.07301903,
                                  'Acc': 58882935.433,
                                  'PublicService': 29595.82500000001,
                                  'BI': 22.266619120000005},
                             'overall': 65.01}}

    window.updateForm([model_res1, model_res2])
    # window.setWindowFlags(Qt.Window)
    window.show()
    sys.exit(app.exec_())
