#  控制输入框
from PyQt5.QtCore import QRegularExpression, QModelIndex, QAbstractItemModel, Qt, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit, QWidget, QDoubleSpinBox, QStyleOptionViewItem, QHBoxLayout, \
    QCheckBox

#  指标权重列checkbox的控制
from qgis.PyQt import QtCore

class CenterCheckBox(QWidget):
    toggled = pyqtSignal(bool)
    def __init__(self, parent):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.check = QCheckBox()
        layout.addWidget(self.check, alignment=Qt.AlignCenter)
        # self.check.setFocusProxy(self)
        self.check.toggled.connect(self.toggled)
        # set a 0 spacing to avoid an empty margin due to the missing text
        # self.check.setStyleSheet('color: red; spacing: 0px;')

    @pyqtProperty(bool, user=True) # note the user property parameter
    def checkState(self):
        return self.check.isChecked()

    @checkState.setter
    def checkState(self, state):
        self.check.setChecked(state)


class singleCheckStateDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, exclude_row=[]):
        self.exclude_row = exclude_row
        super(singleCheckStateDelegate, self).__init__(parent)

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> QWidget:
        if index.row() not in self.exclude_row:
            check = CenterCheckBox(parent)
            check.toggled.connect(lambda: self.commitData.emit(check))
            return check
        else:
            return None
    
    def setEditorData(self, editor: QWidget, index: QtCore.QModelIndex) -> None:
        if index.data(Qt.UserRole) is not None:
            if isinstance(editor, CenterCheckBox):
                editor.checkState = index.data(Qt.UserRole)
        # return super(singleCheckStateDelegate, self).setEditorData(editor, index)
    
    def setModelData(self, editor: QWidget, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> None:
        if isinstance(editor, CenterCheckBox):
            current_data = editor.checkState
            model.setData(index, current_data, Qt.UserRole)
        # return super(singleCheckStateDelegate, self).setModelData(editor, model, index)


# 可以控制LineEdit的输入
class InputLineEditDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(InputLineEditDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setFrame(False)
        reg = QRegularExpression(r"^(0[\.][0-9]{1,2})|1$")
        doubleValidator = QRegularExpressionValidator()
        doubleValidator.setRegularExpression(reg)
        editor.setValidator(doubleValidator)
        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        return super(InputLineEditDelegate, self).setEditorData(editor, index)


#  百分比输入框
class SpinBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, decimals=2, suffix="%"):
        super(SpinBoxDelegate, self).__init__(parent)
        self.decimal = decimals
        self.suffix = suffix

    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(0)
        editor.setMaximum(100)
        editor.setDecimals(self.decimal)
        editor.setSuffix(self.suffix)
        return editor

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        if isinstance(editor, QDoubleSpinBox):
            current_data = editor.textFromValue(editor.value()) + self.suffix
            model.setData(index, current_data, Qt.EditRole)
        else:
            return super(SpinBoxDelegate, self).setModelData(editor, model, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if index.data() is not None:
            current_data = index.data(Qt.EditRole)
            if isinstance(current_data, str):
                current_data = editor.valueFromText(current_data)
            editor.setValue(float(current_data))
        else:
            return super(SpinBoxDelegate, self).setEditorData(editor, index)


class NoEditableDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(NoEditableDelegate, self).__init__(parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        return None