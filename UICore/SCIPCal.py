import os, time
import math
import traceback
import pandas as pd
import numpy as np
from PyQt5.QtCore import pyqtProperty
from qgis._core import QgsVectorFileWriter, QgsProject, QgsVectorLayer
from sqlalchemy import create_engine

from UICore.Gv import model_config_params, model_layer_meta
from sqlalchemy.types import Integer

from UICore.mSqlite import Sqlite
from pyscipopt import Model as scipModel, quicksum

from UICore.log4p import Log

params_file=os.path.join(model_config_params.config_path, model_config_params.param_file)
type_filter = '''type=6 or type=7 or type=8 or type=9'''

log = Log(__name__)

#  模型类
class Model:
    m_db = None
    m_df_land = None
    m_df_match = None
    m_df_grid = None

    def get_field_names(self):
        self.name_area = model_layer_meta.name_potentialLand_area.lower()
        self.name_type = model_layer_meta.name_type.lower()
        self.name_landid = model_layer_meta.name_landid.lower()
        self.name_unitid = model_layer_meta.name_unitid.lower()
        self.name_r_po = model_layer_meta.name_r_po.lower()
        self.name_CurBldAdj = model_layer_meta.name_CurBldAdj.lower()
        self.name_CurRBld = model_layer_meta.name_CurRBld.lower()
        self.name_MetroIf = model_layer_meta.name_MetroIF.lower()
        self.name_PublicService = model_layer_meta.name_PublicService.lower()
        self.name_layer_PotentialLand = model_layer_meta.name_layer_PotentialLand
        self.name_layer_match = model_layer_meta.name_layer_match
        self.name_potentialLand_area = model_layer_meta.name_potentialLand_area
        self.name_plabi = model_layer_meta.name_plabi.lower()
        self.name_io = model_layer_meta.name_io.lower()

    def __init__(self, model_name, db_name, df_constraint, logClass=None):
        self.db_name = db_name
        self.m_db = Sqlite(self.db_name)
        self.get_field_names()
        self.model_name = model_name

        self.df_four_land_cons = df_constraint
        # self.df_four_land_cons = read_excel(params_file, sheet_name=model_config_params.Potential_Constraint,header=0,index_col=0)  # 第一列设为索引
        self.m_df_land = self.read_file(self.name_layer_PotentialLand)
        self.m_df_match = self.read_file(self.name_layer_match)
        self.model = None

        global log
        if logClass is not None:
            log = logClass

    def read_file(self, tbl_name):
        r = self.m_db.execute_dict(
            '''select * from {}
                where {}'''.format(tbl_name, type_filter))
        r = pd.DataFrame.from_dict(r)
        return r

    def create_index(self):
        self.m_db.execute(
            '''CREATE INDEX IF NOT EXISTS  index_type ON {}({})'''.format(self.name_layer_PotentialLand, self.name_type))

        self.m_db.execute(
            '''CREATE INDEX IF NOT EXISTS  index_type ON {}({})'''.format(self.name_layer_match, self.name_type))

        self.m_db.execute(
            '''CREATE INDEX IF NOT EXISTS  index_unitid ON {}({})'''.format(self.name_layer_PotentialLand, self.name_type))

        self.m_db.execute(
            '''CREATE INDEX IF NOT EXISTS  index_landid ON {}({})'''.format(self.name_layer_match, self.name_type))

    def land_summary(self, type):
        LandID_K = self.m_df_land[self.m_df_land[self.name_type]==type].index.tolist()
        area = self.m_df_land[self.m_df_land[self.name_type]==type][self.name_potentialLand_area].sum()
        return LandID_K, area

    def build(self):
        model=scipModel("The Plan of residential building")
        # model.enableReoptimization(True)
        model.hideOutput()

        try:
            self.create_index()

            x = {}
            # LandID,居住专规用地编号
            self.LandIDs = self.m_df_land[self.name_landid].tolist()
            self.m_df_land.set_index(self.name_landid, inplace=True)

            # #Po-地块居住建筑潜力，由地块面积*容积率
            # self.Po = {key: value for key, value in zip(self.LandID, self.gdf_four_land['R_Po'.lower()])}
            # WHEN UnitType='城镇单元' THEN 1
            self.m_df_grid = self.m_db.execute_dict(
                '''SELECT * FROM (
                    SELECT DISTINCT(unitid) AS unitid,
                        (CASE
                            WHEN (bi < 0.3 or bi > 2) and UnitType = '城镇单元' THEN 1
                            ELSE 0 
                         END) AS Unit_IN, 
                        (CurPOP + FixaddPOP) as Unit_CALPOP, weight as Unit_BI_WT, PlaJOB as Unit_FJOB 
                    FROM {}
                    WHERE {}
                ) WHERE Unit_IN = 1
                '''.format(self.name_layer_match, type_filter)
            )
            self.m_df_grid = pd.DataFrame.from_dict(self.m_df_grid)
            self.m_df_grid.set_index(self.name_unitid, inplace=True)

            self.UnitIDs = self.m_df_grid.index.tolist()

            x = {i: model.addVar(vtype='B',name="x(%d)"%(i)) for i in self.LandIDs}

            self.x_Unit_FlexPOP={}
            self.x_Unit_PlaBI={}
            for unitid in self.UnitIDs:
                lst_calids = self.m_df_match[self.m_df_match[self.name_unitid] == unitid].index.to_list()

                self.x_Unit_FlexPOP[unitid]=model.addVar(vtype='C',name="Unit_FlexPOP(%d)"%(unitid))
                model.addCons(self.x_Unit_FlexPOP[unitid]==quicksum(
                    x[self.m_df_match.loc[n, self.name_landid]] * self.m_df_match.loc[n, self.name_r_po] for n in lst_calids) / 35)

                self.x_Unit_PlaBI[unitid]=model.addVar(vtype="C",name="Unit_PlaBI(%d)"%(unitid))
                model.addCons(self.x_Unit_PlaBI[unitid]==(self.x_Unit_FlexPOP[unitid]+self.m_df_grid.loc[unitid, 'Unit_CALPOP'] + 1) /
                              (self.m_df_grid.loc[unitid, 'Unit_FJOB']+1))

            #增加四个决策变量，潜力使用比
            x_K6=model.addVar(vtype='C',
                              lb=self.df_four_land_cons.loc[6,"L_R_Po_R"],
                              ub=self.df_four_land_cons.loc[6,"R_R_Po_R"],
                              name="The 6th Land Ratio")
            x_K7=model.addVar(vtype='C',
                              lb=self.df_four_land_cons.loc[7,"L_R_Po_R"],
                              ub=self.df_four_land_cons.loc[7,"R_R_Po_R"],
                              name="The 7th Land Ratio")
            x_K8=model.addVar(vtype='C',
                              lb=self.df_four_land_cons.loc[8,"L_R_Po_R"],
                              ub=self.df_four_land_cons.loc[8,"R_R_Po_R"],
                              name="The 8th Land Ratio")
            x_K9=model.addVar(vtype='C',
                              lb=self.df_four_land_cons.loc[9,"L_R_Po_R"],
                              ub=self.df_four_land_cons.loc[9,"R_R_Po_R"],
                              name="The 9th Land Ratio")

            LandID_K, area = self.land_summary(6)
            model.addCons(x_K6==quicksum(x[i] * self.m_df_land.loc[i, self.name_area] for i in LandID_K) / area)
            LandID_K, area = self.land_summary(7)
            model.addCons(x_K7==quicksum(x[i] * self.m_df_land.loc[i, self.name_area] for i in LandID_K) / area)
            LandID_K, area = self.land_summary(8)
            model.addCons(x_K8==quicksum(x[i] * self.m_df_land.loc[i, self.name_area] for i in LandID_K) / area)
            LandID_K, area = self.land_summary(9)
            model.addCons(x_K9==quicksum(x[i] * self.m_df_land.loc[i, self.name_area] for i in LandID_K) / area)

            #目标变量-拆迁量，负向指标，越小越好,
            self.x_I_DemoBld=model.addVar(vtype='C',name=model_config_params.Indicator_demo)
            model.addCons(self.x_I_DemoBld==quicksum(x[i]*self.m_df_land.loc[i, self.name_CurBldAdj] for i in self.LandIDs))
            #中间变量
            self.x_I_CurRBld=model.addVar(vtype='C',name="Total current R building area")
            model.addCons(self.x_I_CurRBld==quicksum(x[i]*self.m_df_land.loc[i, self.name_CurRBld] for i in self.LandIDs))

            #中间变量-总建筑量，正向指标，越大越好，参与目标函数
            self.x_I_PlanBld=model.addVar(vtype='C',name="Total increase building area")
            model.addCons(self.x_I_PlanBld==quicksum(x[i]*self.m_df_land.loc[i, self.name_r_po] for i in self.LandIDs))

            #目标变量-轨道交通可达性评价变量，正向指标，越大越好，参与目标函数
            self.x_I_Acc=model.addVar(vtype="C",name=model_config_params.Indicator_acc)
            a = {i: math.log(self.m_df_land.loc[i, self.name_r_po] + 1) * self.m_df_land.loc[i, self.name_MetroIf] for i in self.LandIDs}
            model.addCons(self.x_I_Acc==quicksum(x[i]*a[i] for i in self.LandIDs))
            # self.m_df_land.loc[:,"log_r_po"] = self.m_df_land[self.name_r_po].apply(math.log)
            # model.addCons(self.x_I_Acc==quicksum(x[i]*self.m_df_land.loc[i, "log_r_po"] for i in self.LandIDs))

            #目标变量-公共服务覆盖，正向指标，越大越好，参与目标函数
            self.x_I_PublicServe=model.addVar(vtype="C",name=model_config_params.Indicator_pubService)
            model.addCons(self.x_I_PublicServe==quicksum(x[i]*self.m_df_land.loc[i, self.name_PublicService] for i in self.LandIDs))

            #目标变量-纯新增建筑变量
            self.x_I_NetIncRPo=model.addVar(vtype="C",name=model_config_params.Indicator_net)
            model.addCons(self.x_I_NetIncRPo==self.x_I_PlanBld-self.x_I_CurRBld)

            self.model = model
            self.x = x
            return model
        except:
            log.error(traceback.format_exc())
            return None
        finally:
            model = None

    #保存预生成的参数配置
    def save_preset_params(self):
        #记录5个之指标的最大值和最小值,范围
        #格式-name,max,min，range
        config_path = model_config_params.config_path
        preset_file = model_config_params.PresetPara
        out_path = os.path.join(config_path, preset_file)

        try:
            columns = ["Indicator", "max", "min", "range"]
            para=[]

            res = self.cal_preset('NetIncRPo', self.x_I_NetIncRPo, bMax=True)
            if res is not None:
                para.append(res)
            else:
                raise Exception('NetIncRPo预设值计算错误')

            res = self.cal_preset('Acc', self.x_I_Acc, bMax=True, bMin=True)
            if res is not None:
                para.append(res)
            else:
                raise Exception('Acc预设值计算错误')

            res = self.cal_preset('PublicService', self.x_I_PublicServe, bMax=True, bMin=True)
            if res is not None:
                para.append(res)
            else:
                raise Exception('PublicService预设值计算错误')

            if len(para) == 0:
                raise ValueError("无法完成预设范围参数计算！")
            df_para = pd.DataFrame(para, columns=columns)
            df_para.to_csv(out_path, index=None)
            return True
        except ValueError as e:
            log.error(e)
            return False
        except Exception as e:
            log.error(e)
            return False
        # except IOError as e:
        #     log.error("无法写入{}文件")
        #     return False

    def cal_preset(self, name, obj=None, bMax=False, bMin=False):
        try:
            maxi = 0
            mini = 0

            if bMax:
                maxi = self.model_opt("maximize", obj)
            if bMin:
                mini = self.model_opt("minimize", obj)
            if obj is None:
                raise Exception("决策目标{}为空".format(name))

            if maxi >= 0 and mini >= 0:
                range = maxi-mini
                return [name, maxi, mini, range]
            else:
                return None
        except:
            return None

    def model_opt(self, sense, object=None):
        if self.model is None:
            return None
        if object is None:
            return None

        self.model.setObjective(object, sense)
        opt_sol = self._optmize(object.name, self.model)
        return opt_sol

    def _optmize(self, name, m):
        opti_sol = 0.0
        m.optimize()
        status = m.getStatus()
        if status == "optimal":
            for v in m.getVars():
                if v.name == name:
                    opti_sol = m.getVal(v)
        else:
            log.warning("无法计算出最优结果")
            opti_sol = -1

        self.model.freeTransform()
        return opti_sol

    def load_preset_params(self):
        try:
            # 载入预先计算好的指标信息
            config_path = model_config_params.config_path
            preset_file = model_config_params.PresetPara
            out_path = os.path.join(config_path, preset_file)

            df_para=pd.read_csv(out_path, header=0, index_col=0)

            if df_para.loc["NetIncRPo", "min"] < 0 or df_para.loc["NetIncRPo", "range"] < 0 or \
                df_para.loc["Acc", "min"] < 0  or df_para.loc["Acc", "range"] < 0 or \
                df_para.loc["PublicService", "min"] < 0 or df_para.loc["PublicService", "range"] < 0:

                return None

            # 载入先前设置好的指标权重
            EvaObj=(self.x_I_NetIncRPo-df_para.loc["NetIncRPo", "min"])/df_para.loc["NetIncRPo", "range"] + \
                   (self.x_I_Acc-df_para.loc["Acc", "min"])/df_para.loc["Acc", "range"] + \
                   (self.x_I_PublicServe-df_para.loc["PublicService", "min"])/df_para.loc["PublicService", "range"]
            return EvaObj

        except:
            return None

    def WeightEvaObj(self, EvaObj, w):
        if self.model is None:
            return False

        self.model.setObjective(EvaObj, "maximize")
        self.model.optimize()
        sol_time = self.model.getSolvingTime()
        nsols = self.model.getNSols()  # 记录最优解的个数
        sols = self.model.getSols()    # 记录所有的最优解 list
        log.debug('模型优化计算完毕，共耗时:{}秒. 产生备选方案个数:{}'.format(sol_time, nsols))

        if nsols < 1:
            log.warning("在当前模型中不存在可行解.")
            return False

        sol_list = []
        for i in range(nsols):
            # 首先计算BI 如何
            BI_Score = 0.0
            for j in self.UnitIDs:
                BI = 1 / sols[i][self.x_Unit_PlaBI[j]]
                if 0.3 < BI < 2:
                    BI_Score = BI_Score + self.m_df_grid.loc[j, 'Unit_BI_WT'] * self.m_df_grid.loc[j, 'Unit_IN']
            sol_list.append([sols[i][self.x_I_NetIncRPo],
                             sols[i][self.x_I_DemoBld],
                             sols[i][self.x_I_Acc],
                             sols[i][self.x_I_PublicServe],
                             BI_Score])

        a_sol_list = np.array(sol_list)
        max_demobld = np.max(a_sol_list[:,1], 0)  # 获取方案中的拆除建筑量最大值
        a_sol_list[:, 1] = max_demobld - a_sol_list[:, 1]  # 正向化

        # 进行TOPSIS排序
        sol_score = self.TopsisSols(a_sol_list, w)
        m_sorted = sorted(enumerate(sol_score), key=lambda x:x[1], reverse=True)
        sorted_inds = [m[0] for m in m_sorted]
        sorted_nums = [m[1] for m in m_sorted]
        log.debug(sorted_inds)
        log.debug(sorted_nums)
        # 保存最优值
        bnum = sorted_inds[0]
        log.debug("最佳方案编号: {}".format(bnum))

        res = self.export_result(sorted_inds, sols, sol_list)
        return res

    def export_result(self, sorted_inds, sols, sol_list):
        try:
            # 保存最优值
            Land_IO = []
            Unit_BI = []
            Indicator_value = []
            bnum = sorted_inds[0]

            # 编写函数保存所有结果了 sol[a][x] a=解的编号，x=变量名称
            Indicator_value.append([self.x_I_NetIncRPo.name, sols[bnum][self.x_I_NetIncRPo]])
            Indicator_value.append([self.x_I_DemoBld.name, sols[bnum][self.x_I_DemoBld]])
            Indicator_value.append([self.x_I_Acc.name, sols[bnum][self.x_I_Acc]])
            Indicator_value.append([self.x_I_PublicServe.name, sols[bnum][self.x_I_PublicServe]])
            Indicator_value.append(["BI", sol_list[sorted_inds[0]][4]])

            for i in self.LandIDs:
                Land_IO.append([i, round(sols[bnum][self.x[i]]), self.m_df_land.loc[i, model_layer_meta.name_r_po]])
            for j in self.UnitIDs:
                Unit_BI.append([j, 1 / (sols[bnum][self.x_Unit_PlaBI[j]])])

            df_Land_IO=pd.DataFrame(Land_IO, columns=[model_layer_meta.name_landid, self.name_io,
                                                      model_layer_meta.name_r_po])
            df_Unit_BI=pd.DataFrame(Unit_BI, columns=[model_layer_meta.name_unitid, self.name_plabi])
            df_Indicator_value=pd.DataFrame(Indicator_value, columns=["Indicator", "value"])

            #  join result
            self.join_result_to_origin_layer(df_Land_IO, model_layer_meta.name_layer_PotentialLand,
                                             self.name_io,
                                             model_layer_meta.name_landid, self.name_io, "Integer", 1)
            self.join_result_to_origin_layer(df_Unit_BI, model_layer_meta.name_layer_Grid,
                                             self.name_plabi,
                                             model_layer_meta.name_unitid, self.name_plabi, "Real", -1)

            if not os.path.exists(model_config_params.result_folder):
                os.mkdir(model_config_params.result_folder)
            model_path = os.path.join(model_config_params.result_folder, "model_files")
            if not os.path.exists(model_path):
                os.mkdir(model_path)
            ds_path = os.path.join(model_config_params.result_folder, "model_files", self.model_name)
            if os.path.exists(ds_path):
                ds_path = ds_path + ".sqlite"
            else:
                ds_path = ds_path + time.strftime('%Y-%m-%d-%H-%M-%S') + ".sqlite"

            log.info("导出模型运算结果至模型库{}.".format(ds_path))

            #  导出结果图形
            out_lyr = QgsVectorLayer("{}|layername={}".format(self.db_name, model_layer_meta.name_layer_PotentialLand),
                                                              model_layer_meta.name_layer_PotentialLand, 'ogr')
            # output_file_land = os.path.join(model_path, model_layer_meta.name_layer_PotentialLand)
            # self.write_to_model_files(out_lyr, output_file_land, model_layer_meta.name_layer_PotentialLand)
            self.write_to_model_files(out_lyr, ds_path, model_layer_meta.name_layer_PotentialLand)

            #  导出标准单元图层
            out_lyr = QgsVectorLayer("{}|layername={}".format(self.db_name, model_layer_meta.name_layer_Grid),
                                     model_layer_meta.name_layer_Grid, 'ogr')
            # output_file_grid = os.path.join(model_path, model_layer_meta.name_layer_Grid)
            # self.write_to_model_files(out_lyr, output_file_grid, model_layer_meta.name_layer_Grid)
            self.write_to_model_files(out_lyr, ds_path, model_layer_meta.name_layer_Grid)

            res = ModelResult()
            res.name = self.model_name
            res.dataSource = ds_path
            res.layers = {
                "land": model_layer_meta.name_layer_PotentialLand,
                "grid": model_layer_meta.name_layer_Grid
            }

            #  net increase变量的极值范围
            max_ = (self.m_df_land[self.name_r_po] - self.m_df_land[self.name_CurRBld]).map(
                lambda x: 0 if x < 0 else x
            ).sum()
            cur_ = df_Indicator_value.query('Indicator=="{}"'.format(model_config_params.Indicator_net)).iloc[0, 1]
            res.ranges[model_config_params.Indicator_net] = [0, max_, cur_]

            #  demolish变量的极值范围
            min_ = self.m_df_land[self.name_CurRBld].sum() * -1
            cur_ = df_Indicator_value.query('Indicator=="{}"'.format(model_config_params.Indicator_demo)).iloc[0, 1] * -1
            res.ranges[model_config_params.Indicator_demo] = [min_, 0, cur_]

            #  acc变量的极值范围
            max_ = self.m_df_land.query('{}==1'.format(self.name_MetroIf))[
                "{}".format(self.name_r_po)].sum()

            cur_ = (df_Land_IO[self.name_io] * df_Land_IO[model_layer_meta.name_r_po]).sum()
            # cur_ = df_Indicator_value.query('Indicator=="{}"'.format(model_config_params.Indicator_acc)).iloc[0, 1]
            res.ranges[model_config_params.Indicator_acc] = [0, max_, cur_]

            #  pubService的极值范围
            max_ = self.m_df_land['{}'.format(self.name_PublicService)].sum()
            cur_ = df_Indicator_value.query('Indicator=="{}"'.format(model_config_params.Indicator_pubService)).iloc[0, 1]
            res.ranges[model_config_params.Indicator_pubService] = [0, max_, cur_]

            #  BI的极值范围
            max_ = self.m_df_grid['Unit_BI_WT'].sum()
            cur_ = df_Indicator_value.query('Indicator=="{}"'.format(model_config_params.Indicator_bi)).iloc[0, 1]
            res.ranges[model_config_params.Indicator_bi] = [0, max_, cur_]

            return res
            # df_Indicator_value.to_csv(os.path.join(model_config_params.result_folder, "Indicator_res.csv"), index=None)
            # df_Land_IO.to_csv(os.path.join(model_config_params.result_folder, "Land_IO_res.csv"), index=None)
            # df_Unit_BI.to_csv(os.path.join(model_config_params.result_folder, "Unit_BI_res.csv"), index=None)

        except Exception as e:
            log.error(traceback.format_exc())
            return None

    def join_result_to_origin_layer(self, df_join, origin_lyr, res_lyr,  index_col_name, join_col_name, data_type, default_value):
        engine = create_engine(r'sqlite:///{}'.format(self.db_name), echo=False)
        df_join.to_sql(res_lyr, con=engine, if_exists='replace', index=False,
                          dtype={index_col_name: Integer(), join_col_name: Integer()})

        exec_str = '''
                    ALTER TABLE {} ADD COLUMN {} {}
                '''.format(origin_lyr, join_col_name, data_type)  #  model_layer_meta.name_layer_PotentialLand
        self.m_db.execute(exec_str)

        exec_str = '''
                    update {} set {}={}.{} from {} where {}.{}={}.{}
                '''.format(origin_lyr, join_col_name, res_lyr, join_col_name, res_lyr, origin_lyr, index_col_name,
                           res_lyr, index_col_name)
        self.m_db.execute(exec_str)

        exec_str = '''
                    update {} set {}={} where {} is null
                '''.format(origin_lyr, join_col_name, default_value, join_col_name)
        self.m_db.execute(exec_str)

    #  模型结果图形文件导出到model_files文件夹
    def write_to_model_files(self, layer, output_file, layer_name):
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        # save_options.driverName = 'ESRI Shapefile'
        save_options.driverName = 'SQLite'
        save_options.datasourceOptions = ["SPATIALITE=YES"]
        save_options.layerOptions = ["SPATIAL_INDEX=YES"]
        save_options.layerName = layer_name
        # save_options.layerOptions = ["ENCODING=UTF-8", "2GB_LIMIT=NO"]
        # save_options.fileEncoding = 'UTF-8'
        save_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer # Update mode
        save_options.EditionCapability = QgsVectorFileWriter.CanAddNewLayer
        transform_context = QgsProject.instance().transformContext()
        layer.setProviderEncoding("utf-8")

        error = QgsVectorFileWriter.writeAsVectorFormatV3(layer,
                                                          output_file,
                                                          transform_context,
                                                          save_options)

        if error[0] != QgsVectorFileWriter.NoError:
            save_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile  #Create mode

            error = QgsVectorFileWriter.writeAsVectorFormatV3(layer,
                                                              output_file,
                                                              transform_context,
                                                              save_options)

        if error[0] != QgsVectorFileWriter.NoError:
            raise Exception("创建数据库出错!错误原因:\n{}".format(traceback.format_exc()))

    def TopsisSols(self, mx_Indicator: np.array, w):   # 利用TOPSIS法对最优解集进行排序
        # 此代码是实现TOPSIS综合评价算法
        # 输入数据为mx_Indicator m*n矩阵 m表示m个方案，n表示n个指标
        # 假设所有的指标都经过正向化处理，即指标越大越好
        nw = np.array(w)  # 评价指标权重
        sol_score = []             # 保存方案的得分
        m = mx_Indicator.shape[0]  # 得出方案个数
        sq_indi = mx_Indicator*mx_Indicator   # 将指标值平方计算
        sum_col = np.sum(sq_indi, 0)  # 0对列求和，1对行求和
        sqrt_sum_col = np.sqrt(sum_col)
        # 元素除以列,进行标准化
        z_Indicator = mx_Indicator / sqrt_sum_col
        maxi = np.max(z_Indicator, 0)  # 每一列最大值
        mini = np.min(z_Indicator, 0)  # 每一列最小值
        for i in range(m):
            d1 = np.sqrt(np.sum((z_Indicator[i, :] - maxi) * (z_Indicator[i, :] - maxi) * nw))  # 距离最优解距离
            d2 = np.sqrt(np.sum((z_Indicator[i, :] - mini) * (z_Indicator[i, :] - mini) * nw))  # 距离最劣解距离
            # 方案i 得分
            score = d2 / (d1 + d2)
            sol_score.append(score)
        return sol_score


class ModelResult():
    def __init__(self):
        self._name = ""  # 模型名称
        self._dataSource = ""  # 数据库datasource
        self._layers = {}  # 图形结果的名称

        self._indicators = {}  # 指标计算结果
        self._ranges = {}  # 变量范围值 [min, max, current]

    @pyqtProperty(str)
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        self._name = v

    @pyqtProperty(str)
    def dataSource(self):
        return self._dataSource

    @dataSource.setter
    def dataSource(self, v):
        self._dataSource = v

    @pyqtProperty(dict)
    def layers(self):
        return self._layers

    @layers.setter
    def layers(self, v):
        self._layers = v

    @property
    def indicators(self):
        return self._indicators

    @indicators.setter
    def indicators(self, v):
        self._indicators = v

    @pyqtProperty(dict)
    def ranges(self):
        return self._ranges

    @ranges.setter
    def ranges(self, v):
        self._ranges = v


