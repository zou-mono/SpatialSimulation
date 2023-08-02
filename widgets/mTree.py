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

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def tree_model_currentItemChanged(self, cur_item: QTreeWidgetItem, previous_item: QTreeWidgetItem):
        pass

    @Slot(QItemSelection, QItemSelection)
    def tree_model_selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        if selected.isEmpty():
            return

        selected_count = len(self.selectionModel().selectedIndexes())

        if selected_count > 1:
            # 多选情况下，只要已选中的节点中包括父节点，就不允许选中
            for cur in selected.indexes():
                if cur.parent().data() is None:
                    self.selectionModel().select(cur, QItemSelectionModel.Deselect)

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
