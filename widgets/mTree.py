from PyQt5.QtCore import QItemSelection, QItemSelectionModel, pyqtSlot, pyqtProperty
from PyQt5.QtWidgets import QTreeWidget, QAbstractItemView, QStyleFactory, QTreeWidgetItem
from qgis._gui import QgsLayerTreeView

Slot = pyqtSlot


class Model_Tree(QTreeWidget):
    def __init__(self, parent):
        super(Model_Tree, self).__init__(parent)

        self.setStyle(QStyleFactory.create("windows"))

        self.selectionModel().selectionChanged.connect(self.tree_model_selectionChanged)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

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