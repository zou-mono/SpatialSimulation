from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QWidget
from PyQt5 import QtCore, QtGui
import sys

from UI.UILogView import Ui_frmLogView
from UICore.log4p import Log

Slot = QtCore.pyqtSlot

log = Log(__name__)


class frmLogView(QWidget, Ui_frmLogView):
    def __init__(self, parent=None):
        super(frmLogView, self).__init__(parent=parent)
        self.setupUi(self)

        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)

        log.setLogViewer(parent=parent, logViewer=self.txt_log)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = frmLogView()
    window.setWindowFlags(Qt.Window)
    window.show()
    sys.exit(app.exec_())