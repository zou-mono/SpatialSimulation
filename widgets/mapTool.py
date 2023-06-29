from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QAction, QWidget
from qgis._core import QgsWkbTypes, QgsPoint, QgsPointXY, QgsRectangle, QgsGeometry, QgsVectorLayer, Qgis
from qgis._gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom, QgsMapToolIdentifyFeature, QgsAttributeDialog, \
    QgsMapToolIdentify, QgsMapMouseEvent, QgsRubberBand, QgsMapTool

from UICore.log4p import Log

from UICore.Gv import Tools, Window_titles
from widgets.mDock import mDock
from forms.frmIdentifyResult import frmIdentfiyResult, identifyFeature

Slot = QtCore.pyqtSlot

log = Log(__name__)

bFirstOpenIdentifyDialog = True

class QActionPan(QAction):
    def __init__(self, mapCanvas):
        super(QActionPan, self).__init__()

        # self.actionPan = QAction("平移", parent)
        self.setIconText("平移")
        self.setToolTip("平移")
        self.setEnabled(True)
        self.setIcon(QIcon(QPixmap(":/icons/icons/mActionPan.svg")))

        self.mapCanvas = mapCanvas
        self.triggered.connect(self.pan)
        self.tool = QgsMapToolPan(self.mapCanvas)
        self.tool.setAction(self)

    def pan(self):
        self.mapCanvas.setMapTool(self.tool)


class QActionZoom(QAction):
    def __init__(self, mapCanvas, bZoomOut=False):
        super(QActionZoom, self).__init__()

        self.mapCanvas = mapCanvas
        self.setEnabled(True)

        if bZoomOut:
            self.setIconText("缩小")
            self.setToolTip("缩小")
            self.setIcon(QIcon(QPixmap(":/icons/icons/mActionZoomOut.svg")))
            self.toolZoomOut = QgsMapToolZoom(self.mapCanvas, True)
            self.triggered.connect(self.zoomOut)
        else:
            self.setIconText("放大")
            self.setToolTip("放大")
            self.setIcon(QIcon(QPixmap(":/icons/icons/mActionZoomIn.svg")))
            self.toolZoomIn = QgsMapToolZoom(self.mapCanvas, False)
            self.triggered.connect(self.zoomIn)

    def zoomOut(self):
        self.mapCanvas.setMapTool(self.toolZoomOut)

    def zoomIn(self):
        self.mapCanvas.setMapTool(self.toolZoomIn)


# 扩展mapToolIdentifyFeature,增加拉框选择
class mIdentifyFeature(QgsMapToolIdentify):
    featureIdentified = pyqtSignal(object, object)

    def __init__(self, mapCanvas: QgsMapCanvas):
        super(mIdentifyFeature, self).__init__(mapCanvas)
        self.rubberBand = QgsRubberBand(mapCanvas, QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setFillColor(QColor(254, 178, 76, 63))
        self.rubberBand.setStrokeColor(QColor(254, 58, 29, 100))
        self.mapCanvas = mapCanvas
        self.layers = None
        self.reset()

    def reset(self):
        self.startMapPoint = self.endMapPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)

    def setLayer(self, layers):
        self.layers = layers

    def canvasPressEvent(self, e: QgsMapMouseEvent) -> None:
        # self.startPoint = self.toMapCoordinates(e.pos())
        self.startMapPoint = e.mapPoint()
        self.startCanvasPoint = QgsPointXY(e.pos())
        # self.rubberBand = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)
        self.isEmittingPoint = True
        self.showRect(self.startMapPoint, self.startMapPoint)

    def canvasMoveEvent(self, e: QgsMapMouseEvent) -> None:
        self.endMapPoint = e.mapPoint()
        self.endCanvasPoint = QgsPointXY(e.pos())

        if not self.isEmittingPoint:
            return

        self.showRect(self.startMapPoint, self.endMapPoint)

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        self.isEmittingPoint = False
        self.rubberBand.hide()

        self.layers = self.mapCanvas.layers()

        r = self.rectangle(self.startMapPoint, self.endMapPoint)
        rect = self.rectangle(self.startCanvasPoint, self.endCanvasPoint)

        geom = None
        if rect == 0:
            geom = QgsGeometry().fromPointXY(e.mapPoint())
        elif rect is not None:
            geom = QgsGeometry().fromRect(r)

        if geom is not None:
            self.identifyFromGeometry(geom)

    def identifyFromGeometry(self, geom):
        res = self.identify(geom, self.IdentifyMode.TopDownAll, self.layers, QgsMapToolIdentify.VectorLayer)
        self.featureIdentified.emit(res, self.endMapPoint)

    def showRect(self, startPoint: QgsPointXY, endPoint: QgsPointXY):
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        if startPoint.x() == endPoint.x() and startPoint.y() == endPoint.y():
            return

        point1 = QgsPointXY(startPoint.x(), startPoint.y())
        point2 = QgsPointXY(startPoint.x(), endPoint.y())
        point3 = QgsPointXY(endPoint.x(), endPoint.y())
        point4 = QgsPointXY(endPoint.x(), startPoint.y())

        self.rubberBand.addPoint(point1, False)
        self.rubberBand.addPoint(point2, False)
        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(point4, True)

        self.rubberBand.show()

    def rectangle(self, startPoint: QgsPointXY, endPoint: QgsPointXY):
        if startPoint is None or endPoint is None:
            return None
        elif (startPoint.x() == endPoint.x() and
              startPoint.y() == endPoint.y()):
            return 0

        return QgsRectangle(startPoint, endPoint)

    def deactivate(self) -> None:
        QgsMapTool.deactivate(self)
        self.deactivated.emit()


class QActionIdentifyFeature(QAction):
    def __init__(self, mapCanvas):
        super(QActionIdentifyFeature, self).__init__()

        self.setIconText("要素查询")
        self.setToolTip("要素查询")
        self.setEnabled(True)
        self.setIcon(QIcon(QPixmap(":/icons/icons/mActionIdentify.svg")))

        self.mapCanvas = mapCanvas
        self.tool = mIdentifyFeature(self.mapCanvas)
        self.tool.featureIdentified.connect(self.showFeatures)
        self.triggered.connect(self.identifyFeature)

    def identifyFeature(self, layers):
        self.mapCanvas.setMapTool(self.tool)
        if layers:
            self.tool.setLayer(layers)
        else:
            layers = self.mapCanvas.layers()
            if layers:
                self.tool.setLayer(layers)

        self.layers = layers

    def showFeatures(self, identifyResults: list, endMapPoint: QgsPointXY):
        iLimit = 500

        layers = self.mapCanvas.layers()

        for vlayer in layers:
            vlayer.removeSelection()

        identified_dict = {}
        for f in identifyResults:
            mFeature = identifyFeature(f.mLayer, f.mFeature)
            if f.mLayer not in identified_dict:
                identified_dict[f.mLayer] = [mFeature]
            else:
                if len(identified_dict[f.mLayer]) < iLimit:
                    identified_dict[f.mLayer].append(mFeature)
                else:
                    continue

        for vlayer, features in identified_dict.items():
            ids = [f.id() for f in features]
            vlayer.selectByIds(ids, Qgis.SelectBehavior.AddToSelection)

        dockIdentifyResult = self.mapCanvas.window().dockIdentifyResult
        dockIdentifyResult.clear()
        dockIdentifyResult.updateForm(identified_dict, endMapPoint)
        dockIdentifyResult.show()


class mapTools:
    def __init__(self, mapCanvas: QgsMapCanvas):
        self.mapCanvas = mapCanvas

    def Create(self, toolName: Tools):
        if toolName == Tools.pan:
            return QActionPan(self.mapCanvas)
        elif toolName == Tools.zoomIn:
            return QActionZoom(self.mapCanvas, False)
        elif toolName == Tools.zoomOut:
            return QActionZoom(self.mapCanvas, True)
        elif toolName == Tools.identifyFeature:
            return QActionIdentifyFeature(self.mapCanvas)
