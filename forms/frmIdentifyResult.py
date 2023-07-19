import os

from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QWidget, QTreeWidgetItem, QStyleFactory, QTableWidgetItem, QHeaderView, QAbstractItemView
from qgis._core import QgsPointXY, Qgis

from UI.UIIdentifyResult import Ui_identifyResult
from UICore.Gv import Window_titles, SplitterState, Dock
from UICore.styles import table_default_style
from widgets.mDock import mDock
from PyQt5.QtCore import Qt, QSize, QItemSelectionModel, pyqtSlot
from qgis._gui import QgsMapToolIdentify, QgsFeatureListModel

bFirstOpen = True
info_text = "识别出{}个要素"

Slot = pyqtSlot

class frmIdentfiyResult(QWidget, Ui_identifyResult):
    dockIdentifyResult = None

    def __init__(self, parent=None):
        super(frmIdentfiyResult, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)

        self.resize(self.parent.width() * 0.3, self.parent.width() * 0.3)

        self.dockIdentifyResult = mDock(Window_titles.identifyResult, parent)
        self.dockIdentifyResult.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dockIdentifyResult.setWidget(self)
        parent.addDockWidget(Qt.RightDockWidgetArea, self.dockIdentifyResult)

        self.dockIdentifyResult.setFloating(True)
        self.dockIdentifyResult.hide()

        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setProperty("Stretch", SplitterState.expanded)
        self.splitter.setProperty("Dock", Dock.up)
        self.splitter.setProperty("WidgetToHide", self.tree_result)
        self.splitter.setProperty("ExpandParentForm", False)

        self.splitter.setSizes([150, self.splitter.height() - 140])
        self.resize(self.splitter.width(), self.splitter.height())
        self.splitter.setupUi()

        self.lbl_identifyInfo.setText(info_text.format("0"))

        self.tree_result.setStyle(QStyleFactory.create("windows"))
        self.tree_result.itemClicked.connect(self.tree_result_itemClicked)

        self.lineEdit.setEnabled(False)

        self.tlb_result.setColumnCount(2)
        self.tlb_result.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tlb_result.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tlb_result.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tlb_result.setHorizontalHeaderLabels(["字段名", "值"])
        self.tlb_result.horizontalHeader().setSectionsMovable(False)
        self.tlb_result.horizontalHeader().setStretchLastSection(True)
        self.tlb_result.horizontalHeader().setFixedHeight(20)
        self.tlb_result.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tlb_result.verticalHeader().setDefaultSectionSize(15)  # 高度
        table_default_style(self.tlb_result)  # 设置表格样式

    @Slot(QTreeWidgetItem, int)
    def tree_result_itemClicked(self, item: QTreeWidgetItem, col: int):
        vLayeItem = item.data(col, Qt.UserRole)
        vFeatureItem = item.data(col, QgsFeatureListModel.Role.FeatureRole)

        if vFeatureItem is not None:
            # print(featureItem.attributeMap())
            vFeature = vFeatureItem["feature"]
            vLayer = vFeatureItem["layer"]
            self.add_feature_row_to_table(vFeature)
            vLayer.selectByIds([vFeature.id()], Qgis.SelectBehavior.SetSelection)

        if vLayeItem is not None:
            features = vLayeItem["features"]
            vlayer = vLayeItem["layer"]
            # self.tree_result.setSelection(self.tree_result.visualItemRect(item.child(0)), QItemSelectionModel.Select)
            # item.child(0).setSelected(True)
            # self.tlb_result.setFocus()
            self.add_feature_row_to_table(features[0].mFeature())
            ids = [f.id() for f in features]
            vlayer.selectByIds(ids, Qgis.SelectBehavior.SetSelection)

    def add_feature_row_to_table(self, vFeature):
        irow = 0
        self.tlb_result.setRowCount(0)
        for k, v in vFeature.attributeMap().items():
            self.tlb_result.insertRow(irow)

            newItem = QTableWidgetItem(str(k))
            self.tlb_result.setItem(irow, 0, newItem)
            newItem = QTableWidgetItem(str(v))
            self.tlb_result.setItem(irow, 1, newItem)

            irow += 1

    def updateForm(self, identified_dict: dict, endMapPoint: QgsPointXY):
        self.identified_dict = identified_dict

        iIdentify_count = 0
        iFirst = True
        for vlayer, features in identified_dict.items():
            layItem = QTreeWidgetItem([vlayer.name()])
            d = {
                "layer": vlayer,
                "features": features
            }
            layItem.setData(0, Qt.UserRole, d)
            self.tree_result.addTopLevelItem(layItem)

            for feature in features:
                feature = feature.mFeature()
                child = QTreeWidgetItem([str(feature[vlayer.displayField()])])
                m = {
                    "layer": vlayer,
                    "feature": feature
                }
                child.setData(0, QgsFeatureListModel.Role.FeatureRole, m)
                layItem.addChild(child)
                if iFirst:
                    iFirst = False
                    self.add_feature_row_to_table(feature)
                    self.tree_result.setCurrentItem(child)
                iIdentify_count += 1

        if len(identified_dict) > 1:
            self.tree_result.collapseAll()
        else:
            self.tree_result.expandAll()

        self.lineEdit.setText("{}, {}".format(str(endMapPoint.x()), str(endMapPoint.y())))
        self.lbl_identifyInfo.setText("识别出{}个要素".format(str(iIdentify_count)))

        print(py_dir_path)

    def layerItem(self, layer):
        for i in range(self.tree_result.topLevelItemCount()):
            item = self.tree_result.topLevelItem(i)
            if item is not None:
                if item.data(0, Qt.UserRole).name() == layer.name():
                    return item
        return None

    def clear(self):
        self.tree_result.clear()
        self.tree_result.sortByColumn(-1, Qt.AscendingOrder)

        self.tlb_result.clearContents()
        self.tlb_result.setRowCount(0)

    def sizeHint(self):
        return QSize(400, 500)

    def show(self):
        self.dockIdentifyResult.show()
        super(frmIdentfiyResult, self).show()


# 自定义一个类用来存储字典
class identifyFeature(object):
    def __init__(self, layer, feature):
        self.layer = layer
        self.feature = feature

    def mFeature(self):
        return self.feature

    def id(self):
        return self.feature.id()

    def __hash__(self):
        return hash(self.layer.name())

    def __eq__(self, other):
        if self.layer.name() == other.layer.name():
            return True
        return False


class IdentifyResultsFeatureItem(QTreeWidgetItem):
    def __init__(self, mFields, mFeature, mCrs):
        super(IdentifyResultsFeatureItem, self).__init__()
        self.mFields = mFields
        self.mFeature = mFeature
        self.mCrs = mCrs

    def mFields(self):
        return self.mFields

    def mFeature(self):
        return self. mFeature

    def mCrs(self):
        return self.mCrs
