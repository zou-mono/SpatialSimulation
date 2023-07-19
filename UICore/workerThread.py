from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from UICore.SpModel import modelCal
from UICore.log4p import Log

log = Log(__name__)


class ModelCalWorker(QtCore.QObject):
    modelCal = pyqtSignal(str, object, str, str, object, object, object, object, object)
    finished = pyqtSignal(bool, object)

    def __init__(self):
        super(ModelCalWorker, self).__init__()

    def run(self, model_name, layers, lyr_name_Grid, lyr_name_PotentialLand, vGrid_field, vPotential_field,
            df_constraint, df_indicator_Weight, logClass):
        flag, res = modelCal(model_name, layers, lyr_name_Grid, lyr_name_PotentialLand, vGrid_field, vPotential_field,
                        df_constraint, df_indicator_Weight, logClass)
        self.finished.emit(flag, res)
