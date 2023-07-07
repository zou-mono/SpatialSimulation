# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 15:08:32 2023
决策变量尽量不要放在分母
@author: 周青峰
"""
import os
import sqlite3
import math
import traceback

import pandas as pd

from pandas import read_excel, DataFrame, read_csv

from UICore.Gv import model_config_params
from UICore.SpModel import name_layer_match, name_layer_PotentialLand, name_type, name_potentialLand_area, name_landid, \
    name_unitid, name_r_po, name_CurBldAdj, name_CurRBld, name_MetroIF, name_PublicService
from UICore.log4p import Log
from UICore.mSqlite import Sqlite
from pyscipopt import Model as scipModel, quicksum

from UICore.log4p import Log

# four_land_shape_file=name_layer_PotentialLand
# four_land_unit_shape_file=name_layer_match
params_file=os.path.join(model_config_params.config_path, model_config_params.param_file)
type_filter = '''type=6 or type=7 or type=8 or type=9'''

log = Log(__name__)

class Model:
    m_db = None
    m_df_land = None
    m_df_match = None
    m_df_grid = None

    def get_field_names(self):
        self.name_area = name_potentialLand_area.lower()
        self.name_type = name_type.lower()
        self.landid = name_landid.lower()
        self.unitid = name_unitid.lower()
        self.name_r_po = name_r_po.lower()
        self.name_CurBldAdj = name_CurBldAdj.lower()
        self.name_CurRBld = name_CurRBld.lower()
        self.name_MetroIf = name_MetroIF.lower()
        self.name_PublicService = name_PublicService.lower()

    def __init__(self, db_name):
        self.db_name = db_name
        self.m_db = Sqlite(self.db_name)
        self.df_four_land_cons=read_excel(params_file, sheet_name=model_config_params.Potential_Constraint,header=0,index_col=0) #第一列设为索引
        self.m_df_land=self.read_file(name_layer_PotentialLand)
        self.m_df_match=self.read_file(name_layer_match)
        self.model = None

        self.get_field_names()

    def read_file(self, tbl_name):
        r = self.m_db.execute_dict(
            '''select * from {}
                where {}'''.format(tbl_name, type_filter))
        r = pd.DataFrame.from_dict(r)
        return r

    def create_index(self):
        self.m_db.execute(
            '''CREATE INDEX IF NOT EXISTS  index_type ON {}({})'''.format(name_layer_PotentialLand, self.name_type))

        self.m_db.execute(
            '''CREATE INDEX IF NOT EXISTS  index_type ON {}({})'''.format(name_layer_match, self.name_type))

        self.m_db.execute(
            '''CREATE INDEX IF NOT EXISTS  index_unitid ON {}({})'''.format(name_layer_PotentialLand, self.name_type))

        self.m_db.execute(
            '''CREATE INDEX IF NOT EXISTS  index_landid ON {}({})'''.format(name_layer_match, self.name_type))

    def land_summary(self, type):
        LandID_K = self.m_df_land[self.m_df_land[self.name_type]==type].index.tolist()
        area = self.m_df_land[self.m_df_land[self.name_type]==type][name_potentialLand_area].sum()
        return LandID_K, area

    def build(self):
        model=scipModel("The Plan of residential building")
        # model.enableReoptimization(True)
        model.hideOutput()

        try:
            self.create_index()

            x = {}
            # LandID,居住专规用地编号
            LandID = self.m_df_land[self.landid].tolist()
            self.m_df_land.set_index(self.landid, inplace=True)

            # #Po-地块居住建筑潜力，由地块面积*容积率
            # self.Po = {key: value for key, value in zip(self.LandID, self.gdf_four_land['R_Po'.lower()])}

            self.m_df_grid = self.m_db.execute_dict(
                '''
                    SELECT DISTINCT(unitid) AS unitid,
                        (CASE 
                            WHEN UnitType='城镇单元' THEN 1
                            ELSE 0 
                         END) AS Unit_IN, 
                        (CurPOP + FixaddPOP) as Unit_CALPOP, weight as Unit_BI_WT, PlaJOB as Unit_FJOB 
                    FROM {}
                    where {}
                '''.format(name_layer_match, type_filter)
            )
            self.m_df_grid = pd.DataFrame.from_dict(self.m_df_grid)
            self.m_df_grid.set_index(self.unitid, inplace=True)

            UnitIDs = self.m_df_grid.index.tolist()
            x = {i: model.addVar(vtype='B',name="x(%d)"%(i)) for i in LandID}

            # lst_calids = list(map(lambda n:
            #              self.m_df_match[self.m_df_match['unitid'] == n].index.to_list(),
            #              UnitIDs))

            x_Unit_FlexPOP={}
            x_Unit_PlaBI={}
            for unitid in UnitIDs:
                lst_calids = self.m_df_match[self.m_df_match[self.unitid] == unitid].index.to_list()

                x_Unit_FlexPOP[unitid]=model.addVar(vtype='C',name="Unit_FlexPOP(%d)"%(unitid))
                model.addCons(x_Unit_FlexPOP[unitid]==quicksum(
                    x[self.m_df_match.loc[n, self.landid]] * self.m_df_match.loc[n, self.name_r_po] for n in lst_calids) / 35)

                x_Unit_PlaBI[unitid]=model.addVar(vtype="C",name="Unit_PlaBI(%d)"%(unitid))
                model.addCons(x_Unit_PlaBI[unitid]==(x_Unit_FlexPOP[unitid]+self.m_df_grid.loc[unitid, 'Unit_CALPOP'] + 1) /
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
            self.x_I_DemoBld=model.addVar(vtype='C',name="Total demolish building area")
            model.addCons(self.x_I_DemoBld==quicksum(x[i]*self.m_df_land.loc[i, self.name_CurBldAdj] for i in LandID))
            #中间变量
            self.x_I_CurRBld=model.addVar(vtype='C',name="Total current R building area")
            model.addCons(self.x_I_CurRBld==quicksum(x[i]*self.m_df_land.loc[i, self.name_CurRBld] for i in LandID))

            #中间变量-总建筑量，正向指标，越大越好，参与目标函数
            self.x_I_PlanBld=model.addVar(vtype='C',name="Total increase building area")
            model.addCons(self.x_I_PlanBld==quicksum(x[i]*self.m_df_land.loc[i, self.name_r_po] for i in LandID))

            #目标变量-轨道交通可达性评价变量，正向指标，越大越好，参与目标函数
            self.x_I_Acc=model.addVar(vtype="C",name="Total Metro cover buidling area")
            a = {i: math.log(self.m_df_land.loc[i, self.name_r_po] + 1) * self.m_df_land.loc[i, self.name_MetroIf] for i in LandID}
            model.addCons(self.x_I_Acc==quicksum(x[i]*a[i] for i in LandID))

            #目标变量-公共服务覆盖，正向指标，越大越好，参与目标函数
            self.x_I_PublicServe=model.addVar(vtype="C",name="Total cover public serve area")
            model.addCons(self.x_I_PublicServe==quicksum(x[i]*self.m_df_land.loc[i, self.name_PublicService] for i in LandID))

            #目标变量-纯新增建筑变量
            self.x_I_NetIncRPo=model.addVar(vtype="C",name="Total net increase R building")
            model.addCons(self.x_I_NetIncRPo==self.x_I_PlanBld-self.x_I_CurRBld)

            self.model = model
            return model
        except:
            log.error(traceback.format_exc())
            return None
        finally:
            model = None

    #保存预生成的参数配置
    def SavePreSetPara(self):
        #记录5个之指标的最大值和最小值,范围
        #格式-name,max,min，range
        config_path = model_config_params.config_path
        preset_file = model_config_params.PresetPara
        out_path = os.path.join(config_path, preset_file)

        try:
            columns=["Indicator","max","min","range"]
            para=[]

            res = self.get_preset('NetIncRPo', self.x_I_NetIncRPo, bMax=True)
            if res is not None:
                para.append(res)
            else:
                raise Exception('NetIncRPo预制值计算错误')

            res = self.get_preset('Acc', self.x_I_Acc, bMax=True, bMin=True)
            if res is not None:
                para.append(res)
            else:
                raise Exception('Acc预制值计算错误')

            res = self.get_preset('PublicService', self.x_I_PublicServe, bMax=True, bMin=True)
            if res is not None:
                para.append(res)
            else:
                raise Exception('PublicService预制值计算错误')

            if len(para) == 0:
                raise ValueError("无法完成预制范围参数计算！")
            df_para = pd.DataFrame(para, columns=columns)
            df_para.to_csv(out_path, index=None)
            return True
        except ValueError as e:
            log.error(e)
            return False
        except Exception as e:
            log.error(e)
            return False
        except IOError as e:
            log.error("无法写入{}文件")
            return False

    def get_preset(self, name, obj=None, bMax=False, bMin=False):
        try:
            range = -1
            maxi = 0
            mini = 0

            if bMax:
                maxi = self.model_opt("maximize", obj)
            if bMin:
                mini = self.model_opt("minimize", obj)
            if obj is None:
                raise Exception("决策目标{}为空".format(name))

            if maxi != -1 and mini != -1:
                range = maxi-mini
            return [name, maxi, mini, range]
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
