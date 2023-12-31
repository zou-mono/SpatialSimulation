import os
import time
import traceback
from os.path import basename

from PyQt5.QtCore import Qt, QSize, QThread, QRegularExpression, QModelIndex
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QApplication, QDialogButtonBox, QWidget, QFileDialog, \
    QAbstractButton, QMessageBox, QTableWidget, QComboBox, QTableWidgetItem, \
    QAbstractItemView, QCheckBox, QHBoxLayout, QHeaderView, QStyledItemDelegate, QStyleOptionViewItem, QLineEdit, \
    QItemDelegate, QSpinBox, QDoubleSpinBox
from PyQt5 import QtCore, QtGui
import sys

import pandas as pd
from pandas import DataFrame
from qgis._core import QgsVectorLayer, QgsProject, QgsVectorFileWriter, QgsStyle, QgsSymbol, QgsSimpleFillSymbolLayer, \
    QgsSingleSymbolRenderer, QgsRendererCategory, QgsCategorizedSymbolRenderer

from UI.UIModelCal import Ui_frmModelCal
from UICore.SpModel import modelCal
from UICore.common import get_qgis_style, get_field_index_no_case, get_srs_id
from UICore.log4p import Log
from UICore.DataFactory import workspaceFactory
from osgeo import ogr, gdal
from UICore.Gv import DataType, model_config_params as g_cp, model_layer_meta as g_lm, Weight_neccessary, prop_neccessary, \
    land_type_dict, model_neccessary_field as g_nf
from UICore.renderer import categrorized_renderer, single_renderer, color_land_type
from UICore.styles import table_default_style
from UICore.workerThread import ModelCalWorker

from forms.frmModelBrowser import UI_ModelBrowser as frmModelBrowser
from widgets.mTable import NoEditableDelegate, InputLineEditDelegate, SpinBoxDelegate, singleCheckStateDelegate

Slot = QtCore.pyqtSlot

log = Log(__name__)

tbl_weight_col = 1  # 评价权重列
tbl_prop_col = 1  # 用地使用率列
tbl_single_check_col = 2  # 单目标优化状态列
exclude_single_row = []  # 不参与单目标优化的行

Grid_neccessary_fields = {
    # '标准单元编号': ['UnitID', 'num'],
    g_nf.grid.name_plajob: [g_lm.name_plajob, 'num'],
    # '规划居住建筑总面积': ['PlaBS', 'num'],
    g_nf.grid.name_CurPop: [g_lm.name_CurPop, 'num'],
    g_nf.grid.name_CurJOB: [g_lm.name_CurJOB, 'num'],
    g_nf.grid.name_UnitType: [g_lm.name_UnitType, 'str']
}

Potential_Land_neccessary_fields = {
    # '居住地块编号': ['LandID', 'num'],
    g_nf.land.name_type: [g_lm.name_type, 'num'],
    g_nf.land.name_CurBldAdj: [g_lm.name_CurBldAdj, 'num'],
    g_nf.land.name_CurRBld: [g_lm.name_CurRBld, 'num'],
    g_nf.land.name_r_po: [g_lm.name_r_po, 'num'],
    g_nf.land.name_MetroIF: [g_lm.name_MetroIF, 'num'],
    g_nf.land.name_PublicService: [g_lm.name_PublicService, 'num']
}

class frmModelCal(QWidget, Ui_frmModelCal):
    def __init__(self, parent=None):
        super(frmModelCal, self).__init__(parent=parent)
        self.parent = parent
        self.setupUi(self)

        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("开始寻找方案")
        self.buttonBox.button(QDialogButtonBox.Cancel).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Cancel).setText("取消")

        self.btn_addGridFile.clicked.connect(self.addGridFile_clicked)
        self.btn_addPotentialLandFile.clicked.connect(self.addPotentialLandFile_clicked)
        self.buttonBox.clicked.connect(self.buttonBox_clicked)

        self.tbl_GridField.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 不允许编辑
        self.tbl_PotentialLandField.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.tbl_prop.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.tbl_weight.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # self.validateValue()
        self.bFirstShow = True

        self.input_qLayer_dict = {
            g_lm.name_layer_PotentialLand: "None",
            g_lm.name_layer_Grid: "None"
        }

        self.mapCanvas = parent.mapCanvas

        self.config_path = g_cp.config_path
        self.param_file = g_cp.param_file
        self.param_path = os.path.join(self.config_path, self.param_file)

    #  初始化模型参数
    def init_model_param(self):
        try:
            if os.path.exists(self.param_path):
                # wb = load_workbook(config_path, read_only=True)
                df = pd.read_excel(self.param_path, sheet_name=None)
                lst_names = list(df)

                if g_cp.Potential_Constraint not in lst_names or \
                        g_cp.IndicatorWeight not in lst_names:
                    raise Exception("error")

                self.use_params(self.param_path)
            else:
                log.warning("配置文件{}不存在，创建默认配置文件".format(self.config_path))

                if not os.path.exists(self.config_path):
                    os.mkdir(self.config_path)
                if not os.path.exists(self.param_path):
                    if not self.init_param_file(self.param_path):
                        return
                self.use_params(self.param_path)
        except:
            log.warning("读取参数配置文件{}发生错误，使用默认参数".format(self.config_path))
            try:
                os.remove(self.param_path)
                if not self.init_param_file(self.param_path):
                    return
                self.use_params(self.param_path)
            except IOError:
                log.error("{}被占用，请先关闭文件!".format(self.param_path))
            except:
                log.error(traceback.format_exc())

    def init_param_file(self, param_path):
        write = None
        try:
            write = pd.ExcelWriter(param_path)
            df = pd.DataFrame(
                [{"Type": 6, "AREA": 0, 'R_Po_R': 0.5, 'Precision': 0.01, 'L_R_Po_R': 0.495, 'R_R_Po_R': 0.505},
                 {"Type": 7, "AREA": 0, 'R_Po_R': 0.05, 'Precision': 0.01, 'L_R_Po_R': 0.0495, 'R_R_Po_R': 0.0505},
                 {"Type": 8, "AREA": 0, 'R_Po_R': 0.1, 'Precision': 0.01, 'L_R_Po_R': 0.099, 'R_R_Po_R': 0.101},
                 {"Type": 9, "AREA": 0, 'R_Po_R': 0.3, 'Precision': 0.01, 'L_R_Po_R': 0.297, 'R_R_Po_R': 0.303}])
            df.to_excel(write, sheet_name=g_cp.Potential_Constraint, index=False)

            tList = []
            for key, value in Weight_neccessary.items():
                tList.append({
                    g_lm.name_indicator: key,
                    g_lm.name_weight: 0.2
                })

            df = pd.DataFrame(tList)

            # df = pd.DataFrame([{"Indicator": 'NetIncRPo', "Weight": 0.5},
            #                    {"Indicator": 'DemoBld', "Weight": 0.1},
            #                    {"Indicator": 'Acc', "Weight": 0.1},
            #                    {"Indicator": 'PublicService', "Weight": 0.1},
            #                    {"Indicator": 'BI', "Weight": 0.1}])
            df.to_excel(write, sheet_name=g_cp.IndicatorWeight, index=False)

            return True
        except:
            log.error(traceback.format_exc())
            return False
        finally:
            if write is not None:
                write.close()

    def use_params(self, param_path):
        df = pd.read_excel(param_path, sheet_name=g_cp.Potential_Constraint, header=0, index_col='Type')
        df = self.launder_df_order(df, prop_neccessary)
        irow = 0
        for k, v in land_type_dict.items():
            if k in df.index:
                value = df.loc[k, 'R_Po_R']
            else:   # 除了四类之外的其他类型比例全部设置为1，且不能编辑
                value = 1
            new_item = QTableWidgetItem()
            new_item.setData(Qt.UserRole, value)
            new_item.setData(Qt.EditRole, '{:.2f}'.format(value * 100) + '%')
            self.tbl_prop.setItem(irow, tbl_prop_col, new_item)

            irow += 1

        self.df_constraint = df

        df = pd.read_excel(param_path, sheet_name=g_cp.IndicatorWeight, index_col='Indicator')
        df = self.launder_df_order(df, Weight_neccessary)
        irow = 0
        checkStates = []
        for k in Weight_neccessary.keys():
            value = df.loc[k, 'Weight']
            new_item = QTableWidgetItem(str(value))
            new_item.setData(Qt.EditRole, value)
            self.tbl_weight.setItem(irow, tbl_weight_col, new_item)

            new_item = QTableWidgetItem()
            if irow not in exclude_single_row:
                new_item.setData(Qt.UserRole, True)
                checkStates.append(True)  # 初始化单目标优化全部选中
            else:
                new_item.setData(Qt.UserRole, False)
                checkStates.append(False)  # 被排除的单目标不选中
            self.tbl_weight.setItem(irow, tbl_single_check_col, new_item)

            irow += 1

        #  checkbox一直显示在tbl中
        for row in range(self.tbl_weight.model().rowCount()):
            new_item = self.tbl_weight.item(row, tbl_single_check_col)
            self.tbl_weight.openPersistentEditor(new_item)

        df[g_lm.name_bSingleCal] = checkStates  # 增加一列用于判断是否进行单目标优化
        self.df_indicator_Weight = df

    # 将从excel读取的df顺序和设定字典顺序一致
    def launder_df_order(self, df: DataFrame, dict_: dict):
        new_df = pd.DataFrame(index=dict_.keys(), columns=df.columns)
        for key in dict_.keys():
            new_df.loc[key] = df.loc[key]
        return new_df

    def write_params_to_memory(self):
        # df1 = pd.read_excel(param_path, sheet_name=g_cp.Potential_Constraint)
        # df2 = pd.read_excel(param_path, sheet_name=g_cp.IndicatorWeight)
        irow = 0
        for key, value in prop_neccessary.items():
            v = float(self.tbl_prop.item(irow, tbl_prop_col).data(Qt.UserRole))
            precision = self.df_constraint.loc[key, 'Precision']
            self.df_constraint.loc[key, 'R_Po_R'] = v
            self.df_constraint.loc[key, 'L_R_Po_R'] = v - v * precision
            self.df_constraint.loc[key, 'R_R_Po_R'] = v + v * precision
            irow += 1

        irow = 0
        for key in Weight_neccessary.keys():
            self.df_indicator_Weight.loc[key, 'Weight'] = float(self.tbl_weight.item(irow, tbl_weight_col).data(Qt.EditRole))
            self.df_indicator_Weight.loc[key, g_lm.name_bSingleCal] = \
                self.tbl_weight.item(irow, tbl_single_check_col).data(Qt.UserRole)
            irow += 1

    def update_neccessary_field_name(self, vGrid, vLand):
        g_lm.name_plajob = vGrid[g_nf.grid.name_plajob]
        g_lm.name_CurPop = vGrid[g_nf.grid.name_CurPop]
        g_lm.name_CurJOB = vGrid[g_nf.grid.name_CurJOB]
        g_lm.name_UnitType = vGrid[g_nf.grid.name_UnitType]

        g_lm.name_type = vLand[g_nf.land.name_type]
        g_lm.name_CurBldAdj = vLand[g_nf.land.name_CurBldAdj]
        g_lm.name_CurRBld = vLand[g_nf.land.name_CurRBld]
        g_lm.name_r_po = vLand[g_nf.land.name_r_po]
        g_lm.name_MetroIF = vLand[g_nf.land.name_MetroIF]
        g_lm.name_PublicService = vLand[g_nf.land.name_PublicService]

    # def write_params_to_file(self, param_path):
    #     df1 = pd.read_excel(param_path, sheet_name=g_cp.Potential_Constraint)
    #     df2 = pd.read_excel(param_path, sheet_name=g_cp.IndicatorWeight)
    #
    #     write = pd.ExcelWriter(param_path)
    #
    #     v = float(self.txt_type_csgx.text())
    #     precision = df1.at[0, 'Precision']
    #     df1.loc[0, 'R_Po_R'] = v
    #     df1.loc[0, 'L_R_Po_R'] = v - v * precision
    #     df1.loc[0, 'R_R_Po_R'] = v + v * precision

    #     df1.to_excel(write, sheet_name=g_cp.Potential_Constraint, index=False)
    #     df2.to_excel(write, sheet_name=g_cp.IndicatorWeight, index=False)
    #     write.close()

    def showEvent(self, QShowEvent):
        if self.bFirstShow:
            self.table_init(self.tbl_GridField, ["说明", "字段"], [0.45, 0.5])
            self.table_init(self.tbl_PotentialLandField, ["说明", "字段"], [0.45, 0.5])
            self.table_init_weight(self.tbl_weight)
            self.table_init_prop(self.tbl_prop)

            self.init_model_param()
            self.bFirstShow = False

    def resizeEvent(self, QResizeEvent):
        pass
        # self.table_resize(self.tbl_GridField, [0.45, 0.5])
        # self.table_resize(self.tbl_PotentialLandField, [0.45, 0.5])
        # self.table_resize(self.tbl_weight, [0.7, 0.1, 0.2])
        # self.table_resize(self.tbl_prop, [0.8, 0.15])

    def table_init_weight(self, tbl: QTableWidget):
        self.table_init(self.tbl_weight, ["目标", "权重", "单项优化"], [0.7, 0.1, 0])
        tbl.setRowCount(0)

        irow = 0
        global exclude_single_row
        exclude_single_row = []
        for key, v in Weight_neccessary.items():
            tbl.insertRow(irow)
            newItem = QTableWidgetItem(v[0])
            tbl.setItem(irow, 0, newItem)
            if not v[2]:
                exclude_single_row.append(irow)
            irow += 1

        tbl.setItemDelegateForColumn(0, NoEditableDelegate(tbl))  # 列不允许编辑
        tbl.setItemDelegateForColumn(tbl_weight_col, InputLineEditDelegate(tbl))
        tbl.setItemDelegateForColumn(tbl_single_check_col, singleCheckStateDelegate(tbl, exclude_single_row))

        table_default_style(tbl)

    def table_init_prop(self, tbl: QTableWidget):
        self.table_init(self.tbl_prop, ["类型", "使用率"], [0.8, 0.1])
        tbl.setRowCount(0)

        irow = 0
        for key, v in land_type_dict.items():
            tbl.insertRow(irow)
            newItem = QTableWidgetItem(v)
            tbl.setItem(irow, 0, newItem)
            irow += 1

        tbl.setItemDelegateForColumn(0, NoEditableDelegate(tbl))  # 列不允许编辑
        tbl.setItemDelegateForColumn(tbl_prop_col,
                                     SpinBoxDelegate(parent=tbl, exclude_row=range(4, len(land_type_dict), 1)))

        table_default_style(tbl)

    def table_init(self, tbl: QTableWidget, header_labels, widths):
        col_num = len(header_labels)
        tbl.setColumnCount(col_num)
        tbl.setHorizontalHeaderLabels(header_labels)
        tbl.horizontalHeader().setSectionsMovable(False)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # for i in range(len(widths)):
        #     tbl.setColumnWidth(i, tbl.width() * widths[i])
        table_default_style(tbl)

    def table_resize(self, tbl: QTableWidget, widths):
        for i in range(len(widths)):
            tbl.setColumnWidth(i, tbl.width() * widths[i])

    def sizeHint(self):
        return QSize(self.parent.width() * 0.3, self.parent.height())

    # 标准单元图层
    def addGridFile_clicked(self):
        try:
            status, fileName, layer = self.add_spatial_data(g_lm.name_layer_Grid, self.tbl_GridField, Grid_neccessary_fields)

            if not status:
                self.txt_GridFile.setText("")
                return

            # sty = get_qgis_style()
            single_renderer(layer, color='%d, %d, %d' % (150, 150, 150), outline_color='#232323', opacity=0.2)

            self.txt_GridFile.setText(fileName)
        except:
            log.error(traceback.format_exc())

    # 潜力用地图层
    def addPotentialLandFile_clicked(self):
        try:
            status, fileName, layer = self.add_spatial_data(g_lm.name_layer_PotentialLand, self.tbl_PotentialLandField,
                                                            Potential_Land_neccessary_fields)

            if not status:
                self.txt_PotentialLandFile.setText("")
                return

            # sty = get_qgis_style()
            # if sty is not None:
                # color_ramp = sty.colorRamp("Spectral")
                # if color_ramp is not None:
                #     color_ramp.invert()

            fni, field_name = get_field_index_no_case(layer, g_lm.name_type)
            # fni = layer.dataProvider().fields().indexFromName(g_lm.name_type)
            if fni == -1:
                log.warning("分级渲染图层{}不存在，无法完成渲染!".format(g_lm.name_type))
            else:
                spec_dict = {}
                for type_index in land_type_dict:
                    symbol_layer = QgsSimpleFillSymbolLayer.create({
                        'color': color_land_type[type_index],
                        'outline_color': color_land_type[type_index]
                    })
                    spec_dict[type_index] = symbol_layer

                categrorized_renderer(layer, fni, land_type_dict, field_name, spec_dict=spec_dict)
                # else:
                #     log.warning("Spectral颜色板丢失，无法完成图层渲染！")

            self.txt_PotentialLandFile.setText(fileName)
        except:
            log.error(traceback.format_exc())

    # 将必要字段添加到列表
    def add_neccesary_field_to_item(self, datasource, tbl, neccessary_fileds):
        field_num_list = []
        field_str_list = []
        field_num_list.append("")
        field_str_list.append("")
        layer = datasource.GetLayer(0)
        layerDefn = layer.GetLayerDefn()
        for i in range(layerDefn.GetFieldCount()):
            fieldName = layerDefn.GetFieldDefn(i).GetName()
            if layerDefn.GetFieldDefn(i).GetType() == ogr.OFTInteger or layerDefn.GetFieldDefn(i).GetType() == \
                    ogr.OFTInteger64 or layerDefn.GetFieldDefn(i).GetType() == ogr.OFTReal:
                field_num_list.append(fieldName)
            elif layerDefn.GetFieldDefn(i).GetType() == ogr.OFTString or layerDefn.GetFieldDefn(i).GetType() == \
                    ogr.OFTWideString:
                field_str_list.append(fieldName)

        bValidate_name = True
        bValidate_type = True
        irow = 0
        tbl.setRowCount(0)
        for key, field in neccessary_fileds.items():
            tbl.insertRow(irow)

            newItem = QTableWidgetItem(key)
            tbl.setItem(irow, 0, newItem)

            combo = mComboBox()
            if field[1] == "num":
                combo.addItems(field_num_list)
            elif field[1] == "str":
                combo.addItems(field_str_list)

            field_index = layer.FindFieldIndex(field[0], False)
            if field_index > -1:
                if field[1] == "num":
                    if field[0] not in field_num_list:
                        bValidate_type = False
                elif field[1] == "str":
                    if field[0] not in field_str_list:
                        bValidate_type = False
                combo.setCurrentText(field[0])
            else:
                combo.setCurrentText("")
                bValidate_name = False

            tbl.setCellWidget(irow, 1, combo)

            irow += 1
        del datasource

        return bValidate_name, bValidate_type

    def add_spatial_data(self, lyr_name, tbl, neccessary_fields):
        fileName, fileType = QFileDialog.getOpenFileName(
            self, "选择待转换矢量图层文件", os.getcwd(),
            "ESRI Shapefile(*.shp)")

        if len(fileName) == 0:
            return False, "", None

        wks = workspaceFactory().get_factory(DataType.shapefile)
        datasource = wks.openFromFile(fileName)
        del wks

        if datasource is None:
            log.error("无法读取shp文件！{}".format(fileName), dialog=True)
            tbl.setRowCount(0)
            return False, "", None
        else:
            bValidate_name, bValidate_type = self.add_neccesary_field_to_item(datasource, tbl, neccessary_fields)
            if not bValidate_name and bValidate_type:
                log.error("{}图层缺失必要字段，请补齐！".format(lyr_name), dialog=True)
            elif not bValidate_type and bValidate_name:
                log.error("{}图层字段类型不匹配，请检查！".format(lyr_name), dialog=True)
            elif not bValidate_type and not bValidate_name:
                log.error("{}图层字段缺失必要字段，并且存在字段类型不匹配，请检查！".format(lyr_name), dialog=True)

            layer_name = datasource.GetLayer(0).GetName()

            layer = QgsVectorLayer(fileName, layer_name, 'ogr')
            if not layer.isValid():
                QMessageBox.information(self, '提示', '文件打开失败', QMessageBox.Ok)
                return False, "", None

            del datasource

            if self.input_qLayer_dict[lyr_name] != "None":
                QgsProject.instance().removeMapLayer(self.input_qLayer_dict[lyr_name])
                self.mapCanvas.refresh()

            QgsProject.instance().addMapLayers([layer])
            self.mapCanvas.setLayers([layer])
            self.input_qLayer_dict[lyr_name] = layer.id()
            self.mapCanvas.setExtent(layer.extent())
            self.mapCanvas.refresh()

            return True, fileName, layer

    @Slot(QAbstractButton)
    def buttonBox_clicked(self, button: QAbstractButton):
        ds_Grid = None
        ds_PotentialLand = None

        try:
            if button == self.buttonBox.button(QDialogButtonBox.Ok):
                log.info("模型输入空间数据合规性检查...")

                path_Grid = self.txt_GridFile.text()
                path_PotentialLand = self.txt_PotentialLandFile.text()

                if path_Grid == "" or path_PotentialLand == "":
                    raise IOError("优化传导空间数据未设置！")

                wks = workspaceFactory().get_factory(DataType.shapefile)

                ds_Grid = wks.openFromFile(path_Grid)
                if ds_Grid is None:
                    raise IOError("读取shp文件{}发生错误！".format(path_Grid))

                ds_PotentialLand = wks.openFromFile(path_PotentialLand)
                if ds_PotentialLand is None:
                    raise IOError("读取shp文件{}发生错误！".format(path_PotentialLand))

                self.vGrid_field = self.check_field(ds_Grid, self.tbl_GridField, "标准单元")
                self.vPotential_field = self.check_field(ds_PotentialLand, self.tbl_PotentialLandField, "潜力用地")

                #  更新全局变量名
                self.update_neccessary_field_name(self.vGrid_field, self.vPotential_field)

                lyr_Grid = ds_Grid.GetLayer(0)
                lyr_PotentialLand = ds_PotentialLand.GetLayer(0)

                srs = lyr_Grid.GetSpatialRef()
                g_cp.srs_id = get_srs_id(srs)

                log.info("模型输入参数检查...")
                self.check_model_param()

                self.thread = QThread(self)
                self.modelCalThread = ModelCalWorker()
                self.modelCalThread.moveToThread(self.thread)
                self.modelCalThread.modelCal.connect(self.modelCalThread.run)
                self.modelCalThread.finished.connect(self.threadStop)

                cur_path, filename = os.path.split(os.path.abspath(sys.argv[0]))
                res_path = os.path.join(cur_path, g_cp.result_folder)
                if not os.path.exists(res_path):
                    os.mkdir(res_path)

                self.write_params_to_memory()

                layers = {}
                for key, qlayer_id in self.input_qLayer_dict.items():
                    layers[key] = QgsProject.instance().mapLayer(qlayer_id)

                if self.txt_model_name.text().strip() == "":
                    model_name = "model_" + time.strftime('%Y-%m-%d-%H-%M-%S')
                    log.warning('模型名称为空，使用默认名称{}'.format(model_name))
                else:
                    model_name = self.txt_model_name.text().strip()

                # modelCal(model_name, layers, lyr_Grid.GetName(), lyr_PotentialLand.GetName(),
                #           self.vGrid_field, self.vPotential_field, self.df_constraint, self.df_indicator_Weight, log)

                self.thread.start()
                self.modelCalThread.modelCal.emit(model_name, layers, lyr_Grid.GetName(), lyr_PotentialLand.GetName(),
                                                  self.vGrid_field, self.vPotential_field, self.df_constraint,
                                                  self.df_indicator_Weight, log)

            elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
                self.threadTerminate()
                # self.close()
        except IOError as err:
            log.error("模型无法运算. 原因:{}".format(err), dialog=True)
        except:
            log.error("模型无法运算. 原因:{}".format(traceback.format_exc()), dialog=True)
        finally:
            del ds_Grid
            del ds_PotentialLand

    #  检查空间数据字段合规性
    def check_field(self, ds, tbl, layer_name):
        vfields = {}

        for irow in range(tbl.rowCount()):
            k = tbl.item(irow, 0).text()
            v = tbl.cellWidget(irow, 1).currentText()

            if k == "" or v == "":
                raise IOError('{}图层缺失必要字段"{}"'.format(layer_name, k))

            layer = ds.GetLayer(0)
            field_index = layer.FindFieldIndex(v, False)
            if field_index < 0:
                raise IOError('{}图层不存在字段"{}"'.format(layer_name, v))
            # vfields[k] = field_index
            vfields[k] = v

        return vfields

    #  检查模型参数合规性
    def check_model_param(self):
        irow = 0
        for v in prop_neccessary.values():
            if str(self.tbl_prop.item(irow, 1)).strip() == "":
                raise IOError("{}使用率未设置！".format(v))
            irow += 1

        irow = 0
        for v in Weight_neccessary.values():
            if str(self.tbl_weight.item(irow, tbl_weight_col)).strip() == "":
                raise IOError("{}权重未设置！".format(v[0]))
            irow += 1

    def threadStop(self, bflag=True, model_res=None):
        self.thread.quit()
        if bflag:
            frm = frmModelBrowser(self)
            # frm.clear()
            frm.updateForm([model_res])
            frm.show()
            # QMessageBox.information(self, "提示", "所有操作已完成，详细信息见日志列表.", QMessageBox.Close)
        else:
            QMessageBox.critical(self, "错误", "操作过程中发生异常，详细信息见日志列表.", QMessageBox.Close)

    def threadTerminate(self):
        try:
            if self.thread is None:
                return

            if self.thread.isRunning():
                self.thread.terminate()
                self.thread.wait()
                del self.thread
            else:
                self.thread.quit()
                self.thread.wait()
        except:
            return


class mComboBox(QComboBox):
    def __init__(self):
        super(mComboBox, self).__init__()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, e: QtGui.QWheelEvent) -> None:
        return


if __name__ == '__main__':
    ogr.UseExceptions()
    app = QApplication(sys.argv)
    # style = QStyleFactory.create("windows")
    # app.setStyle(style)
    window = frmModelCal()
    window.setWindowFlags(Qt.Window)
    window.show()
    sys.exit(app.exec_())
