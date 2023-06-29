#!/usr/bin/env python
from PyQt5.QtWidgets import QSplitter, QWidget, QSplitterHandle, QApplication, QToolButton
from PyQt5.QtCore import Qt, QObject, QEvent, QRect, QPoint, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QPainter, QResizeEvent, QPalette, QPainterPath, QMouseEvent, QShowEvent
from UICore.Gv import Dock, SplitterState

class CollapsibleSplitter(QSplitter):
    def __init__(self, parent, *args):
        super(CollapsibleSplitter, self).__init__(parent, *args)
        self.parent = parent
        self.setOpaqueResize(True)
        self.minDistanceToEdge = 20  # 到边缘的最小距离
        self.splitterState = SplitterState.expanded
        self.bSplitterButton = False
        self.setHandleWidth(10)
        self.bExpandParentForm = False

        self.splitterMoved.connect(self.splitterMoveHandle)

    @pyqtProperty(bool)
    def SplitterButton(self):
        return self.bSplitterButton

    @SplitterButton.setter
    def SplitterButton(self, value):
        self.bSplitterButton = value

    @pyqtProperty(bool)
    def ExpandParentForm(self):
        return self.bExpandParentForm

    @ExpandParentForm.setter
    def ExpandParentForm(self, value):
        self.bExpandParentForm = value

    @pyqtProperty(SplitterState)
    def Stretch(self):
        return self.splitterState

    @Stretch.setter
    def Stretch(self, value):
        self.splitterState = value

    @pyqtProperty(Dock)
    def Dock(self):
        return self.dock

    @Dock.setter
    def Dock(self, value):
        self.dock = value

    @pyqtProperty(QWidget)
    def WidgetToHide(self):
        return self.widgetToHide

    @WidgetToHide.setter
    def WidgetToHide(self, value: QWidget):
        self.widgetToHide = value

    def showEvent(self, a0: QShowEvent) -> None:
        # self.setupUi()
        pass

    def setupUi(self):
        self.handlePos = self.sizes()

        if self.widget(0).objectName() == self.widgetToHide.objectName():
            self.otherWidget = self.widget(1)
        else:
            self.otherWidget = self.widget(0)

        self.hide_num = self.indexOf(self.widgetToHide)

        #  控制最小边缘距离
        if self.dock == Dock.up or self.dock == Dock.down:
            self.setOrientation(Qt.Vertical)
            self.widgetToHide.setMinimumHeight(self.minDistanceToEdge)
            self.otherWidget.setMinimumHeight(self.minDistanceToEdge)
        else:
            self.setOrientation(Qt.Horizontal)
            self.widgetToHide.setMinimumWidth(self.minDistanceToEdge)
            self.otherWidget.setMinimumWidth(self.minDistanceToEdge)

        self.widgetToHide.setMouseTracking(True)
        self.otherWidget.setMouseTracking(True)
        self.setMouseTracking(True)

        if self.splitterState == SplitterState.collapsed:
            self.handleSplitterButton(SplitterState=SplitterState.expanded)

        if self.bSplitterButton:
            self.button = QToolButton(self.parentWidget())
            self.button.clicked.connect(lambda: self.handleSplitterButton(self.splitterState))

    def eventFilter(self, obj: QObject, event: QEvent):
        # print(event.type())
        # if event.type() == QEvent.MouseMove:
        #     print("move")
        # if event.type() == QEvent.KeyPress:
        #     print("key presss")
        # if event.type() == QEvent.MouseButtonPress:
        #     print("press")

        return super().eventFilter(obj, event)

    def handleSplitterButton(self, SplitterState=SplitterState.expanded):
        # if not all(self.splitter.sizes()):
        #     self.splitter.setSizes([1, 1])
        self.setChildrenCollapsible(True)

        # print(self.sizes())
        if SplitterState == SplitterState.expanded:
            self.handlePos = self.sizes()  # 记下展开时的位置，如果再次展开回到这个位置

            if self.bExpandParentForm:
                if self.dock == Dock.left or self.dock == Dock.right:
                    self.hideLen = self.widgetToHide.width()
                    self.window().resize(self.window().width() - self.hideLen, self.window().height())
                else:
                    self.hideLen = self.widgetToHide.height()
                    self.window().resize(self.window().width(), self.window().height() - self.hideLen)

            if self.dock == Dock.up or self.dock == Dock.left:
                self.setSizes([0, 1])
            else:
                self.setSizes([1, 0])

            self.splitterState = SplitterState.collapsed
        else:
            if not self.bExpandParentForm:
                self.setSizes(self.handlePos)  # 1, 0
            else:
                if self.dock == Dock.up or self.dock == Dock.left:
                    otherLen = self.sizes()[1]
                else:
                    otherLen = self.sizes()[0]

                if self.dock == Dock.left or self.dock == Dock.right:
                    # otherLen = self.sizes()[1] if hide_num == 0 else self.sizes()[0]
                    self.window().resize(self.window().width() + self.hideLen, self.window().height())
                else:
                    self.window().resize(self.window().width(), self.window().height() + self.hideLen)

                if self.dock == Dock.up or self.dock == Dock.left:
                    self.setSizes([self.hideLen, otherLen])
                else:
                    self.setSizes([otherLen, self.hideLen])

            self.splitterState = SplitterState.expanded

        if self.bSplitterButton:
            self.setBtnIcon()
            self.setBtnPos()

        # if self.splitterState == SplitterState.collapsed:
        #     self.setEnabled(False)
        # else:
        #     self.setEnabled(True)

    def splitterMoveHandle(self, pos, index):
        if self.orientation() == Qt.Horizontal:
            w = self.width()
        else:
            w = self.height()
        if pos > self.minDistanceToEdge or pos < w - self.minDistanceToEdge:
            self.setChildrenCollapsible(False)

            # if self.splitterState == SplitterState.collapsed:
            #     hide_num = self.indexOf(self.widgetToHide)
            #     if self.Dock == Dock.up or self.Dock == Dock.left:
            #         self.setSizes([1, 0]) if hide_num == 0 else self.setSizes([0, 1])
            #     else:
            #         self.setSizes([0, 1]) if hide_num == 0 else self.setSizes([1, 0])

        if self.bSplitterButton:
            self.setBtnPos()

    def createButton(self, width, height):
        self.button.setFocusPolicy(Qt.NoFocus)
        self.button.setMinimumSize(5, 15)
        self.button.resize(width, height)

        if self.dock == Dock.up:
            self.button.setArrowType(Qt.UpArrow)
        elif self.dock == Dock.down:
            self.button.setArrowType(Qt.DownArrow)
        elif self.dock == Dock.left:
            self.button.setArrowType(Qt.LeftArrow)
        elif self.dock == Dock.right:
            self.button.setArrowType(Qt.RightArrow)
        self.setBtnPos()

    def setBtnIcon(self):
        if self.button.arrowType() == Qt.LeftArrow:
            self.button.setArrowType(Qt.RightArrow)
        elif self.button.arrowType() == Qt.RightArrow:
            self.button.setArrowType(Qt.LeftArrow)
        elif self.button.arrowType() == Qt.UpArrow:
            self.button.setArrowType(Qt.DownArrow)
        elif self.button.arrowType() == Qt.DownArrow:
            self.button.setArrowType(Qt.UpArrow)

    def setBtnPos(self):
        if (self.dock == Dock.up and self.splitterState == SplitterState.expanded) or \
                (self.dock == Dock.down and self.splitterState == SplitterState.collapsed):
            self.button.move((self.widgetToHide.width() - self.button.width()) / 2,
                             self.handle(1).pos().y() - self.button.height())
        elif (self.dock == Dock.up and self.splitterState == SplitterState.collapsed) or \
                (self.dock == Dock.down and self.splitterState == SplitterState.expanded):
                self.button.move((self.widgetToHide.width() - self.button.width()) / 2,
                                 self.handle(1).pos().y() + self.handle(1).height())
        elif (self.dock == Dock.right and self.splitterState == SplitterState.expanded) or \
                (self.dock == Dock.left and self.splitterState == SplitterState.collapsed):
            self.button.move(self.handle(1).pos().x() + self.handle(1).width(),
                             (self.widgetToHide.height() - self.button.height()) / 2)
        elif (self.dock == Dock.right and self.splitterState == SplitterState.collapsed) or \
                (self.dock == Dock.left and self.splitterState == SplitterState.expanded):
            self.button.move(self.handle(1).pos().x() - self.button.width(),
                             (self.widgetToHide.height() - self.button.height()) / 2)

    # def resizeEvent(self, a0: QResizeEvent):
    #     self.resize(a0.size())

    def createHandle(self):
        handle = SplitterHandle(self.orientation(), self)
        return handle


class SplitterHandle(QSplitterHandle):
    handleClicked = pyqtSignal()

    def __init__(self, Orientation, qSplitter: CollapsibleSplitter):
        super(SplitterHandle, self).__init__(Orientation, qSplitter)
        self.splitter = qSplitter

        self.barLength = 115

        self.bBarHover = False  # handle上的按钮默认没有激活
        self.setMouseTracking(True)
        self.bClick = False  # 判断鼠标是否点下

    def paintEvent(self, event):
        # 绘制默认的样式
        super(SplitterHandle, self).paintEvent(event)
        r = self.rect()

        # 绘制顶部扩展按钮
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self.splitter.orientation() == Qt.Vertical:
            # 画按钮矩形
            self.rr = QRect(int(r.x() + (r.width() - self.barLength)/2), r.y(), self.barLength, self.height())

            painter.fillRect(self.rr.x(), self.rr.y() + 1, self.barLength, self.height() - 2,
                             self.palette().color(QPalette.Window))

            # 画两条竖线
            painter.setPen(self.palette().color(QPalette.Dark))
            painter.drawLine(self.rr.x(), self.rr.y() + 1, self.rr.x(), self.rr.y() + self.rr.height() - 2)
            painter.drawLine(self.rr.x() + self.rr.width(), self.rr.y() + 1, self.rr.x() + self.rr.width(), self.rr.y() + self.rr.height() - 2)

            # 画箭头
            painter.fillPath(self.ArrowPointArray(self.rr.x() + 2, self.rr.y() + 3),
                             self.palette().color(QPalette.Dark))
            painter.fillPath(self.ArrowPointArray(self.rr.x() + self.rr.width() - 8, self.rr.y() + 3),
                             self.palette().color(QPalette.Dark))

            # 画装饰点
            x = self.rr.x() + 14
            y = self.rr.y() + 4
            i = 0
            while i < 30:
                painter.setPen(self.palette().color(QPalette.Midlight))
                painter.drawRect(x + 1 + i * 3, y, 1, 1)
                painter.setPen(self.palette().color(QPalette.Dark))
                painter.drawRect(x + i * 3, y - 1, 1, 1)
                i = i + 1
                painter.setPen(self.palette().color(QPalette.Midlight))
                painter.drawRect(x + 1 + i * 3, y + 2, 1, 1)
                painter.setPen(self.palette().color(QPalette.Dark))
                painter.drawRect(x + i * 3, y + 1, 1, 1)

        elif self.splitter.orientation() == Qt.Horizontal:
            # 画按钮矩形
            self.rr = QRect(r.x(), int(r.y() + (r.height() - self.barLength)/2), self.width(), self.barLength)

            painter.fillRect(self.rr.x() + 1, self.rr.y(), self.width() - 2, self.barLength,
                             self.palette().color(QPalette.Window))

            # 画两条竖线
            painter.setPen(self.palette().color(QPalette.Dark))
            painter.drawLine(self.rr.x() + 1, self.rr.y(), self.rr.x() + self.rr.width() - 2, self.rr.y())
            painter.drawLine(self.rr.x() + 1, self.rr.y() + self.rr.height(),
                             self.rr.x() + self.rr.width() - 2, self.rr.y() + self.rr.height())

            # 画箭头
            painter.fillPath(self.ArrowPointArray(self.rr.x() + 2, self.rr.y() + 3),
                             self.palette().color(QPalette.Dark))
            painter.fillPath(self.ArrowPointArray(self.rr.x() + 2, self.rr.y() + self.rr.height() - 8),
                             self.palette().color(QPalette.Dark))

            # 画装饰点
            x = self.rr.x() + 4
            y = self.rr.y() + 14
            i = 0
            while i < 30:
                painter.setPen(self.palette().color(QPalette.Midlight))
                painter.drawRect(x, y + 1 + i * 3, 1, 1)
                painter.setPen(self.palette().color(QPalette.Dark))
                painter.drawRect(x - 1, y + i * 3, 1, 1)
                i = i + 1
                painter.setPen(self.palette().color(QPalette.Midlight))
                painter.drawRect(x + 2, y + 1 + i * 3, 1, 1)
                painter.setPen(self.palette().color(QPalette.Dark))
                painter.drawRect(x + 1, y + i * 3, 1, 1)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.bMove = False
        self.bMove = False if self.bBarHover else True

        if not self.splitter.bSplitterButton:
            # print(event.pos())
            if self.rr.x() <= event.pos().x() <= self.rr.x() + self.rr.width() and \
                    self.rr.y() <= event.pos().y() <= self.rr.y() + self.rr.height():
                self.setCursor(Qt.PointingHandCursor)
                self.bBarHover = True
            else:
                if self.splitter.splitterState == SplitterState.expanded:
                    if self.splitter.orientation() == Qt.Horizontal:
                        self.setCursor(Qt.SplitHCursor)
                    else:
                        self.setCursor(Qt.SplitVCursor)

                    self.bMove = True

                    if self.splitter.splitterState == SplitterState.expanded:
                        if self.bClick and not self.bBarHover:
                            pos = self.splitter.mapFromGlobal(event.globalPos())
                            if self.splitter.orientation() == Qt.Horizontal:
                                pos_move = pos.x()
                            else:
                                pos_move = pos.y()

                            self.splitter.setRubberBand(pos_move)
                        else:
                            return
                else:
                    self.unsetCursor()
                    return
                self.bBarHover = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.bClick = True
        if self.rr.x() <= event.pos().x() <= self.rr.x() + self.rr.width() and \
                self.rr.y() <= event.pos().y() <= self.rr.y() + self.rr.height():
            self.bBarHover = True
        else:
            self.bBarHover = False

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.splitter.setRubberBand(-1)
        super(SplitterHandle, self).mouseReleaseEvent(event)
        if self.bBarHover and not self.bMove:
            self.splitter.handleSplitterButton(self.splitter.splitterState)
            self.bBarHover = False
            self.handleClicked.emit()
        else:
            if self.splitter.splitterState == SplitterState.expanded and not self.bBarHover:
                pos = self.splitter.mapFromGlobal(event.globalPos())
                if self.splitter.orientation() == Qt.Horizontal:
                    pos_move = pos.x()
                    l = self.splitter.width()
                else:
                    pos_move = pos.y()
                    l = self.splitter.height()
                # print(pos_move)
                if self.splitter.minDistanceToEdge <= pos_move <= l - self.splitter.minDistanceToEdge:
                    self.moveSplitter(pos_move)
                elif pos_move < self.splitter.minDistanceToEdge:
                    self.moveSplitter(self.splitter.minDistanceToEdge)
                elif pos_move > l - self.splitter.minDistanceToEdge:
                    self.moveSplitter(l - self.splitter.minDistanceToEdge)
        self.bClick = False

    def ArrowPointArray(self, x, y):
        path = QPainterPath()

        # 右箭头
        if (self.splitter.dock == Dock.right and self.splitter.splitterState == SplitterState.expanded and not self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.left and self.splitter.splitterState == SplitterState.collapsed and not self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.right and self.splitter.splitterState == SplitterState.collapsed and self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.left and self.splitter.splitterState == SplitterState.expanded and self.splitter.bExpandParentForm):
            path.moveTo(x, y)
            path.lineTo(x + 3, y + 3)
            path.lineTo(x, y + 6)

        # 左箭头
        elif (self.splitter.dock == Dock.right and self.splitter.splitterState == SplitterState.collapsed and not self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.left and self.splitter.splitterState == SplitterState.expanded and not self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.right and self.splitter.splitterState == SplitterState.expanded and self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.left and self.splitter.splitterState == SplitterState.collapsed and self.splitter.bExpandParentForm):
            path.moveTo(x + 3, y)
            path.lineTo(x, y + 3)
            path.lineTo(x + 3, y + 6)

        # 上箭头
        elif (self.splitter.dock == Dock.up and self.splitter.splitterState == SplitterState.expanded and not self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.down and self.splitter.splitterState == SplitterState.collapsed and not self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.up and self.splitter.splitterState == SplitterState.collapsed and self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.down and self.splitter.splitterState == SplitterState.expanded and self.splitter.bExpandParentForm):
            path.moveTo(x + 3, y)
            path.lineTo(x + 6, y + 3)
            path.lineTo(x, y + 3)

        # 下箭头
        elif (self.splitter.dock == Dock.up and self.splitter.splitterState == SplitterState.collapsed and not self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.down and self.splitter.splitterState == SplitterState.expanded and not self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.up and self.splitter.splitterState == SplitterState.expanded and self.splitter.bExpandParentForm) or \
                (self.splitter.dock == Dock.down and self.splitter.splitterState == SplitterState.collapsed and self.splitter.bExpandParentForm):
            path.moveTo(x, y)
            path.lineTo(x + 6, y)
            path.lineTo(x + 3, y + 3)

        return path


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    splitter = CollapsibleSplitter()
    splitter.show()
    sys.exit(app.exec_())
