from PyQt5.QtWidgets import QWidget, QTreeWidgetItem, QStyleFactory

from UI.UIIdentifyResult import Ui_identifyResult
from UICore.Gv import Window_titles, SplitterState, Dock
from widgets.mDock import mDock
from PyQt5.QtCore import Qt, QSize
from qgis._gui import QgsMapToolIdentify, QgsFeatureListModel

bFirstOpen = True
info_text = "识别出{}个要素"


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

    def update(self, identified_dict: dict):
        self.identified_dict = identified_dict

        for vlayer, features in identified_dict.items():
            # layItem = self.layerItem(vlayer)

            # if layItem is not None:
            #     layItem.setData(0, Qt.UserRole, vlayer)
            #     self.tree_result.addTopLevelItem(layItem)
            # else:
            layItem = QTreeWidgetItem([vlayer.name()])
            layItem.setData(0, Qt.UserRole, vlayer)
            self.tree_result.addTopLevelItem(layItem)

            for feature in features:
                feature = feature.mFeature()
                child = QTreeWidgetItem([str(feature[vlayer.displayField()])])
                child.setData(0, QgsFeatureListModel.FeatureRole, feature)
                layItem.addChild(child)

        if len(identified_dict) > 1:
            self.tree_result.collapseAll()
        else:
            self.tree_result.expandAll()

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
