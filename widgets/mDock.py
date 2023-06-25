from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtCore import Qt


class mDock(QDockWidget):
    def __init__(self, *args):
        super(mDock, self).__init__(*args)

        self.topLevelChanged.connect(self.dockSetWinFlags)
        # self.visibilityChanged.connect(self.activeDock)

    def dockSetWinFlags(self, toplevel):
        #  用来重绘dock窗口，使其始终在taskbar之上
        if toplevel:
            self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
            self.show()

    def toggleViewAction(self):
        q = super(mDock, self).toggleViewAction()
        q.triggered.connect(self.showTab)
        return q

    #  保证每次tab打开的时候自动跳转
    def showTab(self, checked):
        if checked:
            self.show()

    def show(self):
        super(mDock, self).show()
        self.raise_()

