from multiprocessing import cpu_count
import os, time
import math
import traceback
import uuid

import pandas as pd
import numpy as np
from PyQt5.QtCore import pyqtProperty
from qgis._core import QgsVectorFileWriter, QgsProject, QgsVectorLayer
from sqlalchemy import create_engine

from UICore.Gv import model_config_params as g_cp, model_layer_meta as g_lm
from sqlalchemy.types import Integer

from UICore.mSqlite import Sqlite
from pyscipopt import Model as scipModel, quicksum

from UICore.log4p import Log

params_file=os.path.join(g_cp.config_path, g_cp.param_file)
type_filter = '''type=6 or type=7 or type=8 or type=9'''
fix_type_filter = '''type<>6 and type <>7 and type<>8 and type<>9'''

log = Log(__name__)

sense_max = 'maximize'
sense_min = 'minimize'

#  模型类
class Model:
    m_db = None
    m_df_land = None
    m_df_match = None
    m_df_grid = None

    def get_field_names(self):
        self.name_area = g_lm.name_potentialLand_area.lower()
        self.name_type = g_lm.name_type.lower()
        self.name_landid = g_lm.name_landid.lower()
        self.name_unitid = g_lm.name_unitid.lower()
        self.name_r_po = g_lm.name_r_po.lower()
        self.name_CurBldAdj = g_lm.name_CurBldAdj.lower()
        self.name_CurRBld = g_lm.name_CurRBld.lower()
        self.name_MetroIf = g_lm.name_MetroIF.lower()
        self.name_PublicService = g_lm.name_PublicService.lower()
        self.name_layer_PotentialLand = g_lm.name_layer_PotentialLand
        self.name_layer_match = g_lm.name_layer_match
        self.name_potentialLand_area = g_lm.name_potentialLand_area
        self.name_plabi = g_lm.name_plabi.lower()
        self.name_io = g_lm.name_io.lower()

    def __init__(self, model_name, db_name, df_indicator_Weight, df_constraint, logClass=None):
        self.db_name = db_name
        self.m_db = Sqlite(self.db_name)
        self.get_field_names()
        self.model_name = model_name

        self.df_constraint = df_constraint
        self.df_weight = df_indicator_Weight
        # self.df_four_land_cons = read_excel(params_file, sheet_name=g_cp.Potential_Constraint,header=0,index_col=0)  # 第一列设为索引
        self.m_df_land = self.read_file(self.name_layer_PotentialLand)
        self.m_df_match = self.read_file(self.name_layer_match)
        self.model = None
        self.model_res = None

        self.obj_dict = {} # 用于存储单目标优化的目标函数, 结构： {变量名称{:变量, :sense}}

        global log
        if logClass is not None:
            log = logClass

    #  针对每个目标求解的综合评分
    def overall(self):
        for sol_key, sol_value in self.model_res.score.items():
            self.df_weight['score'] = -1
            sol_value = sol_value['current']
            for k, v in sol_value.items():
                cur_score = (v - self.model_res.ranges[k][0]) / \
                            (self.model_res.ranges[k][1] - self.model_res.ranges[k][0])
                self.df_weight.loc[k, 'score'] = cur_score

            sol_score = (self.df_weight.loc[:, 'score'] * self.df_weight.loc[:, g_lm.name_weight]).sum() / \
                        self.df_weight.loc[:, g_lm.name_weight].sum()

            self.model_res.score[sol_key]['overall'] = round(sol_score * 100, 2)

    def single_obj(self, name):
        if self.obj_dict is not None:
            if name in self.obj_dict:
                return self.obj_dict[name]['obj'], self.obj_dict[name]['sense']
            else:
                return None, None
        else:
            return None, None

    def read_file(self, tbl_name, filter=type_filter):
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
        model.setParam('limits/maxsol', 30)
        model.setParam('lp/threads', cpu_count() - 1)

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
                              lb=self.df_constraint.loc[6, "L_R_Po_R"],
                              ub=self.df_constraint.loc[6, "R_R_Po_R"],
                              name="The 6th Land Ratio")
            x_K7=model.addVar(vtype='C',
                              lb=self.df_constraint.loc[7, "L_R_Po_R"],
                              ub=self.df_constraint.loc[7, "R_R_Po_R"],
                              name="The 7th Land Ratio")
            x_K8=model.addVar(vtype='C',
                              lb=self.df_constraint.loc[8, "L_R_Po_R"],
                              ub=self.df_constraint.loc[8, "R_R_Po_R"],
                              name="The 8th Land Ratio")
            x_K9=model.addVar(vtype='C',
                              lb=self.df_constraint.loc[9, "L_R_Po_R"],
                              ub=self.df_constraint.loc[9, "R_R_Po_R"],
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
            self.x_I_DemoBld=model.addVar(vtype='C',name=g_cp.Indicator_demo)
            self.obj_dict[g_cp.Indicator_demo] = {
                'obj': self.x_I_DemoBld,
                'sense': sense_min
            }
            model.addCons(self.x_I_DemoBld==quicksum(x[i]*self.m_df_land.loc[i, self.name_CurBldAdj] for i in self.LandIDs))
            #中间变量
            self.x_I_CurRBld=model.addVar(vtype='C',name="Total current R building area")
            model.addCons(self.x_I_CurRBld==quicksum(x[i]*self.m_df_land.loc[i, self.name_CurRBld] for i in self.LandIDs))

            #中间变量-总建筑量，正向指标，越大越好，参与目标函数
            self.x_I_PlanBld=model.addVar(vtype='C',name="Total increase building area")
            model.addCons(self.x_I_PlanBld==quicksum(x[i]*self.m_df_land.loc[i, self.name_r_po] for i in self.LandIDs))

            #目标变量-轨道交通可达性评价变量，正向指标，越大越好，参与目标函数
            self.x_I_Acc=model.addVar(vtype="C",name=g_cp.Indicator_acc)
            self.obj_dict[g_cp.Indicator_acc] = {
                'obj': self.x_I_Acc,
                'sense': sense_max
            }
            a = {i: math.log(self.m_df_land.loc[i, self.name_r_po] + 1) * self.m_df_land.loc[i, self.name_MetroIf] for i in self.LandIDs}
            model.addCons(self.x_I_Acc==quicksum(x[i]*a[i] for i in self.LandIDs))
            # self.m_df_land.loc[:,"log_r_po"] = self.m_df_land[self.name_r_po].apply(math.log)
            # model.addCons(self.x_I_Acc==quicksum(x[i]*self.m_df_land.loc[i, "log_r_po"] for i in self.LandIDs))

            #目标变量-公共服务覆盖，正向指标，越大越好，参与目标函数
            self.x_I_PublicServe=model.addVar(vtype="C",name=g_cp.Indicator_pubService)
            self.obj_dict[g_cp.Indicator_pubService] = {
                'obj': self.x_I_PublicServe,
                'sense': sense_max
            }
            model.addCons(self.x_I_PublicServe==quicksum(x[i]*self.m_df_land.loc[i, self.name_PublicService] for i in self.LandIDs))

            #目标变量-纯新增建筑变量
            self.x_I_NetIncRPo=model.addVar(vtype="C",name=g_cp.Indicator_net)
            self.obj_dict[g_cp.Indicator_net] = {
                'obj': self.x_I_NetIncRPo,
                'sense': sense_max
            }
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
        config_path = g_cp.config_path
        preset_file = g_cp.PresetPara
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
                maxi = self.model_opt(sense_max, obj)
            if bMin:
                mini = self.model_opt(sense_min, obj)
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
            config_path = g_cp.config_path
            preset_file = g_cp.PresetPara
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

    #  目标优化计算
    #  type='multiple'表示多目标优化，type='s_{name}'为具体name的单目标优化
    def execute_obj(self, type=g_cp.Indicator_multi, EvaObj=None, sense=sense_max, w=None,
                    io_field=g_lm.name_io.lower(), bi_field=g_lm.name_plabi.lower()):
        try:
            if self.model is None:
                return False

            sorted_inds, sols, sol_list = self.model_feasibles(EvaObj, sense, w)

            if sols is None:
                return None
            else:
                if self.model_res is None:
                    self.model_res = self.create_model_result()
                self.model_res = self.export_result_to_temp(type, self.model_res, sorted_inds, sols,
                                                            sol_list, io_field, bi_field)
            return self.model_res
        except:
            return None
        finally:
            self.model.freeTransform()

    #  计算所有可行解，并根据TOPSIS算法选取最优解
    def model_feasibles(self, obj, sense=sense_min, w=None):
        if w is None:
            w = []
        self.model.setObjective(obj, sense)
        self.model.optimize()
        sol_time = self.model.getSolvingTime()
        nsols = self.model.getNSols()  # 记录最优解的个数
        sols = self.model.getSols()    # 记录所有的最优解 list
        log.debug('模型优化计算完毕，共耗时:{}秒. 产生备选方案个数:{}'.format(sol_time, nsols))

        if nsols < 1:
            log.warning("在当前模型中不存在可行解.")
            return None, None, None

        sol_list = []
        for i in range(nsols):
            # 首先计算BI 如何
            BI_Score = 0.0
            for j in self.UnitIDs:
                BI = 1 / sols[i][self.x_Unit_PlaBI[j]]
                if 0.3 < BI < 2:
                    BI_Score = BI_Score + self.m_df_grid.loc[j, 'Unit_BI_WT'] * self.m_df_grid.loc[j, 'Unit_IN']

            # 这里是顺序必须要和Weight_neccessary保持一致
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

        return sorted_inds, sols, sol_list

    def fix_indicator_value(self):
        fix_values = {}
        #  模型结果要把其他14类都考虑进来，重新计算14类固定部分的数据
        df_land = self.read_file(self.name_layer_PotentialLand, fix_type_filter)
        df_land.set_index(self.name_landid, inplace=True)

        df_grid = self.m_db.execute_dict(
            '''SELECT * FROM (
                SELECT DISTINCT(unitid) AS unitid,
                    (CASE
                        WHEN (bi < 0.3 or bi > 2) and UnitType = '城镇单元' THEN 1
                        ELSE 0 
                     END) AS Unit_IN, weight as Unit_BI_WT 
                FROM {}
                WHERE {}
            ) WHERE Unit_IN = 1
            '''.format(self.name_layer_match, fix_type_filter)
        )
        df_grid = pd.DataFrame.from_dict(df_grid)
        df_grid.set_index(self.name_unitid, inplace=True)

        value = (df_land[self.name_r_po] - df_land[self.name_CurRBld]).map(
            lambda x: 0 if x < 0 else x
        ).sum()
        fix_values[g_cp.Indicator_net] = value

        value = df_land[self.name_CurRBld].sum()
        fix_values[g_cp.Indicator_demo] = value

        value = df_land.query('{}==1'.format(self.name_MetroIf))[
            "{}".format(self.name_r_po)].sum()
        fix_values[g_cp.Indicator_acc] = value

        value = df_land['{}'.format(self.name_PublicService)].sum()
        fix_values[g_cp.Indicator_pubService] = value

        value = df_grid['Unit_BI_WT'].sum()
        fix_values[g_cp.Indicator_bi] = value

        return fix_values

    # 创建一个模型结果对象
    def create_model_result(self):
        res = ModelResult()
        _id = str(uuid.uuid1())
        res.ID = _id
        res.name = self.model_name
        res.layers = {
            "land": g_lm.name_layer_PotentialLand,
            "grid": g_lm.name_layer_Grid
        }

        if not os.path.exists(g_cp.result_folder):
            os.mkdir(g_cp.result_folder)
        model_path = os.path.join(g_cp.result_folder, "model_files")
        if not os.path.exists(model_path):
            os.mkdir(model_path)
        ds_path = os.path.join(g_cp.result_folder, "model_files", self.model_name)
        if os.path.exists(ds_path + ".sqlite"):
            ds_path = ds_path + "_" + _id + ".sqlite"
        else:
            ds_path = ds_path + ".sqlite"

        res.dataSource = ds_path

        fix_values = self.fix_indicator_value()
        self.fix_values = fix_values

        #  net increase变量的极值范围
        max_ = (self.m_df_land[self.name_r_po] - self.m_df_land[self.name_CurRBld]).map(
            lambda x: 0 if x < 0 else x
        ).sum()
        res.ranges[g_cp.Indicator_net] = [0, max_ + fix_values[g_cp.Indicator_net]]

        #  demolish变量的极值范围
        min_ = self.m_df_land[self.name_CurRBld].sum() * -1
        res.ranges[g_cp.Indicator_demo] = [min_ + fix_values[g_cp.Indicator_demo] * -1, 0]

        #  acc变量的极值范围
        max_ = self.m_df_land.query('{}==1'.format(self.name_MetroIf))[
            "{}".format(self.name_r_po)].sum()
        res.ranges[g_cp.Indicator_acc] = [0, max_ + fix_values[g_cp.Indicator_acc]]

        #  pubService的极值范围
        max_ = self.m_df_land['{}'.format(self.name_PublicService)].sum()
        res.ranges[g_cp.Indicator_pubService] = [0, max_ + fix_values[g_cp.Indicator_pubService]]

        #  BI的极值范围
        max_ = self.m_df_grid['Unit_BI_WT'].sum()
        res.ranges[g_cp.Indicator_bi] = [0, max_ + fix_values[g_cp.Indicator_bi]]

        res.score = {}

        return res

    #  io_field和bi_field是需要挂接的临时表名和临时字段名， 临时表和临时字段同名
    def export_result_to_temp(self, type, res, sorted_inds, sols, sol_list, io_field, bi_field):
        try:
            ds_path = res.dataSource

            if type != g_cp.Indicator_multi:
                obj_key = type.split("_")[1]
            else:
                obj_key = g_cp.Indicator_multi

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
                Land_IO.append([i, round(sols[bnum][self.x[i]]), self.m_df_land.loc[i, g_lm.name_r_po]])
            for j in self.UnitIDs:
                Unit_BI.append([j, 1 / (sols[bnum][self.x_Unit_PlaBI[j]])])

            df_Land_IO=pd.DataFrame(Land_IO, columns=[g_lm.name_landid, io_field,
                                                      g_lm.name_r_po])
            df_Unit_BI=pd.DataFrame(Unit_BI, columns=[g_lm.name_unitid, bi_field])
            df_Indicator_value=pd.DataFrame(Indicator_value, columns=["Indicator", "value"])

            #  join result
            self.join_result_to_origin_layer(df_Land_IO, g_lm.name_layer_PotentialLand,
                                             io_field,
                                             g_lm.name_landid, io_field, "Integer", 1)
            self.join_result_to_origin_layer(df_Unit_BI, g_lm.name_layer_Grid,
                                             bi_field,
                                             g_lm.name_unitid, bi_field, "Real", -1)

            cur = {}
            #  net increase变量的当前值
            cur_ = df_Indicator_value.query('Indicator=="{}"'.format(g_cp.Indicator_net)).iloc[0, 1]
            cur[g_cp.Indicator_net] = cur_ + self.fix_values[g_cp.Indicator_net]

            #  demolish变量的当前值
            cur_ = df_Indicator_value.query('Indicator=="{}"'.format(g_cp.Indicator_demo)).iloc[0, 1] * -1
            cur[g_cp.Indicator_demo] = cur_ + self.fix_values[g_cp.Indicator_demo] * -1

            #  acc变量的当前值
            cur_ = (df_Land_IO[io_field] * df_Land_IO[g_lm.name_r_po]).sum()
            cur[g_cp.Indicator_acc] = cur_ + self.fix_values[g_cp.Indicator_acc]

            #  pubService的极值范围
            cur_ = df_Indicator_value.query('Indicator=="{}"'.format(g_cp.Indicator_pubService)).iloc[0, 1]
            cur[g_cp.Indicator_pubService] = cur_ + self.fix_values[g_cp.Indicator_pubService]

            #  BI的极值范围
            cur_ = df_Indicator_value.query('Indicator=="{}"'.format(g_cp.Indicator_bi)).iloc[0, 1]
            cur[g_cp.Indicator_bi] = cur_ + self.fix_values[g_cp.Indicator_bi]

            res.score[obj_key] = {
                'current': cur,
                'overall': -1
            }

            return res
        except Exception as e:
            log.error(traceback.format_exc())
            return None

    #  导出结果图形
    def export_spatial_layer(self, ds_path):
        out_lyr = QgsVectorLayer("{}|layername={}".format(self.db_name, g_lm.name_layer_PotentialLand),
                                 g_lm.name_layer_PotentialLand, 'ogr')
        # output_file_land = os.path.join(model_path, g_lm.name_layer_PotentialLand)
        # self.write_to_model_files(out_lyr, output_file_land, g_lm.name_layer_PotentialLand)
        self.write_to_model_files(out_lyr, ds_path, g_lm.name_layer_PotentialLand)

        #  导出标准单元图层
        out_lyr = QgsVectorLayer("{}|layername={}".format(self.db_name, g_lm.name_layer_Grid),
                                 g_lm.name_layer_Grid, 'ogr')
        # output_file_grid = os.path.join(model_path, g_lm.name_layer_Grid)
        # self.write_to_model_files(out_lyr, output_file_grid, g_lm.name_layer_Grid)
        self.write_to_model_files(out_lyr, ds_path, g_lm.name_layer_Grid)

    def join_result_to_origin_layer(self, df_join, origin_lyr, res_lyr,  index_col_name, join_col_name, data_type, default_value):
        engine = create_engine(r'sqlite:///{}'.format(self.db_name), echo=False)
        df_join.to_sql(res_lyr, con=engine, if_exists='replace', index=False,
                          dtype={index_col_name: Integer(), join_col_name: Integer()})

        exec_str = '''
                    ALTER TABLE {} ADD COLUMN {} {}
                '''.format(origin_lyr, join_col_name, data_type)  #  g_lm.name_layer_PotentialLand
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
        self._id = -1  # 模型唯一ID
        self._name = ""  # 模型名称
        self._dataSource = ""  # 数据库datasource
        self._layers = {}  # 图形结果的名称

        self._indicators = {}  # 指标计算结果
        self._ranges = {}  # 变量范围值 [min, max]
        self._score = {}

    @pyqtProperty(str)
    def ID(self):
        return self._id

    @ID.setter
    def ID(self, v):
        self._id = v

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

    @pyqtProperty(dict)
    def score(self):
        return self._score

    @score.setter
    def score(self, v):
        self._score = v


