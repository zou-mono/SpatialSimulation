from PyQt5.QtCore import QItemSelection, QItemSelectionModel, pyqtSlot, pyqtProperty, Qt, QPoint
from PyQt5.QtGui import QCursor, QPixmap, QIcon
from PyQt5.QtWidgets import QTreeWidget, QAbstractItemView, QStyleFactory, QTreeWidgetItem, QMenu, QAction
from qgis._gui import QgsLayerTreeView

Slot = pyqtSlot


class Model_Tree(QTreeWidget):
    def __init__(self, parent):
        super(Model_Tree, self).__init__(parent)

        self.parent = parent
        self.setStyle(QStyleFactory.create("windows"))

        self.selectionModel().selectionChanged.connect(self.tree_model_selectionChanged)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_contextMenuRequested)

        # self.currentItemChanged.connect(self.tree_model_currentItemChanged)
        # self.itemSelectionChanged.connect(self.tree_model_selectionChanged)

    def setTocView(self, value):
        if isinstance(value, QgsLayerTreeView):
            self.tocView = value

    # @Slot(QTreeWidgetItem, QTreeWidgetItem)
    # def tree_model_currentItemChanged(self, cur_item: QTreeWidgetItem, previous_item: QTreeWidgetItem):
    #     pass

    @Slot(QItemSelection, QItemSelection)
    def tree_model_selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
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
            # 多选情况下，如果已选中节点中包含root节点，则不允许选中当前节点
            if bhave_root and selected_count > 1:
                self.selectionModel().select(cur_selected, QItemSelectionModel.Deselect)

    def on_contextMenuRequested(self, pos: QPoint):
        selected_count = len(self.selectionModel().selectedIndexes())

        if selected_count > 1:
            context_menu = QMenu()
            context_menu.addAction(QActionModelCompare(self))
            context_menu.exec(QCursor.pos())


#  模型对比
class QActionModelCompare(QAction):
    def __init__(self, parent):
        super(QActionModelCompare, self).__init__("方案对比", parent)
        self.setIconText("方案对比")
        self.setToolTip("方案对比")
        self.setIcon(QIcon(QPixmap(":/icons/icons/方案对比.svg")))
        self.setEnabled(True)
