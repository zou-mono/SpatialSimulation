from PyQt5.QtCore import QItemSelection, QItemSelectionModel, pyqtSlot, pyqtProperty, Qt, QPoint, QEvent
from PyQt5.QtGui import QCursor, QPixmap, QIcon, QKeyEvent, QFont
from PyQt5.QtWidgets import QTreeWidget, QAbstractItemView, QStyleFactory, QTreeWidgetItem, QMenu, QAction
from PyQt5.uic.properties import QtGui
from qgis.PyQt import QtCore
from qgis._core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer, QgsLayerTreeNode
from qgis._gui import QgsLayerTreeView, QgsMapCanvas, QgsLayerTreeMapCanvasBridge

from UICore.Gv import modelRole, toc_groups, model_layer_meta as g_lm, model_config_params as g_cp

Slot = pyqtSlot


class Model_Tree(QTreeWidget):
    def __init__(self, parent):
        super(Model_Tree, self).__init__(parent)

        self.parent = parent
        self.setStyle(QStyleFactory.create("windows"))

        self.selectionModel().selectionChanged.connect(self.on_selectionChanged)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_contextMenuRequested)
        # self.currentItemChanged.connect(self.on_currentItemChanged)
        self.itemSelectionChanged.connect(self.on_itemSelectionChanged)
        self.bMultiSelect = False

        self.node_dict = {}  # 用来存储tocView上已经加载的图层，如果有重复的就不再加载

    def setMapModel(self, bridge):
        if isinstance(bridge, QgsLayerTreeMapCanvasBridge):
            self.bridge = bridge
            self.project = bridge.mapCanvas().project()
            self.mapCanvas = bridge.mapCanvas()
            self.root = self.project.layerTreeRoot()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self.bMultiSelect = False
        if event.key() == Qt.Key_Control:
            self.bMultiSelect = True
        super(Model_Tree, self).keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control:
            self.bMultiSelect = False
        super(Model_Tree, self).keyReleaseEvent(event)

    # @Slot(QTreeWidgetItem, QTreeWidgetItem)
    # def on_currentItemChanged(self, cur_item: QTreeWidgetItem, previous_item: QTreeWidgetItem):
    def on_itemSelectionChanged(self):
        if len(self.selectionModel().selectedIndexes()) != 1:  # 如果是多选不处理
            return

        if self.bMultiSelect:
            return

        cur_item = self.currentItem()

        if cur_item is None:
            return

        if cur_item.parent() is None:
            return

        cur_model = cur_item.data(0, modelRole.model)
        cur_solution = cur_item.data(0, modelRole.solution)['key']
        cur_solution_name = cur_item.data(0, modelRole.solution)['name']

        cur_ds = cur_model.dataSource
        lyr_land_name = cur_model.layers[cur_solution]['land']
        lyr_grid_name = cur_model.layers[cur_solution]['grid']

        node_key = cur_model.ID + "_" + cur_solution
        node_name = cur_solution_name + "_" + cur_model.name

        self.project.removeAllMapLayers()

        layers = []
        for key, group_name in toc_groups.items():
            if key == g_lm.name_io:
                lyr = QgsVectorLayer("{}|layername={}".format(cur_ds, lyr_land_name), node_name, 'ogr')
            else:
                lyr = QgsVectorLayer("{}|layername={}".format(cur_ds, lyr_grid_name), node_name, 'ogr')
            # node_key = node_key + "_" + key
            # if node_key in self.node_dict:
            #     return
            # else:
            #     if key == g_lm.name_io:
            #         lyr = QgsVectorLayer("{}|layername={}".format(cur_ds, lyr_land_name), node_name, 'ogr')
            #     else:
            #         lyr = QgsVectorLayer("{}|layername={}".format(cur_ds, lyr_grid_name), node_name, 'ogr')
            #     self.node_dict[node_key] = lyr

            if lyr.isValid():
                cur_group = self.root.findGroup(group_name)
                self.project.addMapLayer(lyr, False)
                cur_group.insertLayer(0, lyr)
                layers.append(lyr)
                cur_group.setItemVisibilityChecked(True)
                # cur_group.setExpanded(False)
                self.mapCanvas.setExtent(lyr.extent())

        if len(layers) > 0:
            self.mapCanvas.setLayers(layers)
            self.mapCanvas.refresh()
        # print(cur_solution)

    @Slot(QItemSelection, QItemSelection)
    def on_selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        if selected.isEmpty():
            return

        selected_count = len(self.selectionModel().selectedIndexes())
        cur_selected = selected.indexes()[0]

        # 判断选中的节点中是否有root节点
        bhave_root = False
        for cur in self.selectionModel().selectedIndexes():
            if cur.parent().data() is None:
                bhave_root = True
                break

        # 极端情况，当前选中的节点超过1个，把选中的节点中所有root节点都剔除
        if len(selected.indexes()) > 1:
            for cur in self.selectionModel().selectedIndexes():
                if cur.parent().data() is None:
                    self.selectionModel().select(cur, QItemSelectionModel.Deselect)
        else:
            # 如果已选中节点中包含root节点，则不允许选中当前节点
            if bhave_root and selected_count > 1:
                self.selectionModel().select(cur_selected, QItemSelectionModel.Deselect)

    def on_contextMenuRequested(self, pos: QPoint):
        selected_count = len(self.selectionModel().selectedIndexes())
        index =  self.indexAt(pos)

        if selected_count > 1:
            context_menu = QMenu()
            context_menu.addAction(QActionModelCompare(self))
            context_menu.exec(QCursor.pos())
        elif index.parent().data() is None and selected_count == 1:
            context_menu = QMenu()
            context_menu.addAction(QActionModelInfo(self))
            context_menu.exec(QCursor.pos())

#  模型对比
class QActionModelCompare(QAction):
    def __init__(self, parent):
        super(QActionModelCompare, self).__init__("方案对比", parent)
        self.setIconText("方案对比")
        self.setToolTip("方案对比")
        self.setIcon(QIcon(QPixmap(":/icons/icons/方案对比.svg")))
        self.setEnabled(True)

class QActionModelInfo(QAction):
    def __init__(self, parent):
        super(QActionModelInfo, self).__init__("模型信息", parent)
        self.setIconText("模型信息")
        self.setToolTip("模型信息")
        self.setIcon(QIcon(QPixmap(":/icons/icons/information.svg")))
        self.setEnabled(True)
