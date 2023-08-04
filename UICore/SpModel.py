import os
import sys
import time
import traceback

from osgeo import gdal, ogr
from qgis._core import QgsVectorFileWriter, QgsProject

from UICore.DataFactory import workspaceFactory
from UICore.Gv import DataType, model_layer_meta as g_lm, model_config_params as g_cp,\
    indicator_translate_dict, Weight_neccessary
from UICore.SCIPCal import Model
from UICore.common import get_srs_id
from UICore.log4p import Log

log = Log(__name__)

success_log_color = "#3399ff"  # 右侧Logviewer中info日志的突出显示为蓝色


def modelCal(model_name, layers, lyr_name_Grid, lyr_name_PotentialLand, vGrid_field, vPotential_field,
             df_constraint, df_indicator_Weight, logClass=None):
    wks = None
    datasource = None

    global log
    if logClass is not None:
        log = logClass

    lyr_name_Grid = g_lm.name_layer_Grid
    lyr_name_PotentialLand = g_lm.name_layer_PotentialLand

    cur_path, filename = os.path.split(os.path.abspath(sys.argv[0]))
    temp_sqliteDB_name = '%s' % (time.strftime('%Y-%m-%d-%H-%M-%S'))
    temp_sqliteDB_path = os.path.join(cur_path, "tmp")

    try:
        start = time.time()

        if not os.path.exists(temp_sqliteDB_path):
            os.mkdir(temp_sqliteDB_path)

        output_file = os.path.join(temp_sqliteDB_path, temp_sqliteDB_name)

        create_temp_sqliteDB_by_qgis(layers[g_lm.name_layer_Grid], output_file, g_lm.name_layer_Grid)
        datasource = create_temp_sqliteDB_by_qgis(layers[g_lm.name_layer_PotentialLand],
                                                  output_file, g_lm.name_layer_PotentialLand, bOpen=True)

        # create_temp_sqliteDB(temp_sqliteDB_path, temp_sqliteDB_name, path_Grid, lyr_name_Grid)
        # datasource = create_temp_sqliteDB(temp_sqliteDB_path, temp_sqliteDB_name, path_PotentialLand, lyr_name_PotentialLand, bOpen=True)

        if datasource is not None:
            ds_name = datasource.GetName()
            log.info("创建临时数据库{}成功！".format(ds_name), color=success_log_color)

            log.info("开始计算模型输入指标...", color=success_log_color)
            field_cal(datasource, lyr_name_Grid, vGrid_field, lyr_name_PotentialLand, vPotential_field)
            log.info("模型输入指标计算完毕.", color=success_log_color)

            log.info("构建优化传导模型...", color=success_log_color)
            model = Model(model_name, ds_name, df_indicator_Weight,  df_constraint, log)
            model.build()
            # log.info("优化传导模型构建完毕.", color=success_log_color)
            log.info("载入模型预设参数...", color=success_log_color)
            bFlag = model.save_preset_params()
            # bFlag = True
            # preset_params = model.load_preset_params()
            # if preset_params is None:
            #     # log.warning("读取模型预设参数文件失败，尝试重建文件...")
            #     log.warning("模型预设参数文件未找到，系统将重新生成...")
            #     bFlag = model.save_preset_params()

            if bFlag:
                obj_names = []

                preset_params = model.load_preset_params()
                # log.info("模型预制参数载入成功！", color=success_log_color)

                # 这里的顺序是和Weight_neccessary一致的
                w = df_indicator_Weight[g_lm.name_weight].tolist()
                log.info("开始模型优化计算...", color=success_log_color)
                log.info("多目标模型优化计算...")
                model.execute_obj(EvaObj=preset_params, w=w)
                obj_names.append(g_cp.Indicator_multi)

                if len(df_indicator_Weight.query('{}==True'.format(g_lm.name_bSingleCal))) > 0:
                    for index, row in df_indicator_Weight.iterrows():
                        checkState = row[g_lm.name_bSingleCal]
                        if checkState:
                            # single_key = row[g_lm.name_indicator]
                            log.info("单目标模型优化计算:{}".format(indicator_translate_dict[index]))
                            obj, sense = model.single_obj(index)
                            # no = Weight_neccessary[index][1]   # 取编号
                            # io_field = g_lm.name_io + "_" + str(no)
                            # bi_field = g_lm.name_plabi + "_" + str(no)
                            # model.execute_obj('s_' + index,  obj, sense, w, io_field=io_field, bi_field=bi_field)
                            model.execute_obj('s_' + index,  obj, sense, w)
                            obj_names.append(index)

                log.info("综合评分计算...")
                model.overall()  # 综合评分
                ds_path = model.model_res.dataSource
                log.info("所有模型优化计算步骤完毕，正在导出至模型库...",
                         color=success_log_color)

                model.export_spatial_layer(ds_path, obj_names)
                model.release()

                end = time.time()
                log.info("完成所有计算步骤，共耗时：{}秒. 结果保存在模型库{}".format(
                    "{:.2f}".format(end - start), os.path.abspath(ds_path)))
                return True, model.model_res
            else:
                raise Exception("无法完成模型计算，请检查数据和参数设置！")
        else:
            raise IOError("打开临时数据库失败！")
    except Exception as err:
        log.error(traceback.format_exc())
        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # log.error(traceback.format_exception(exc_type, exc_value, exc_traceback, 1))
        return False, None
    finally:
        del wks
        del datasource
        # remove_temp_sqliteDB(temp_sqliteDB_path, temp_sqliteDB_name)


# 自动更新计算模型运算所必须的字段
def field_cal(dataSource, lyr_name_Grid, vGrid_field, lyr_name_PotentialLand, vPotential_field):
    exec_res = None

    lyr_Grid = dataSource.GetLayer(lyr_name_Grid)
    lyr_PotentialLand = dataSource.GetLayer(lyr_name_PotentialLand)

    try:
        #  标准单元编号
        create_new_field(lyr_Grid, g_lm.name_unitid, ogr.OFTInteger64)
        exec_str = r"UPDATE {} SET {}=ROWID".format(lyr_name_Grid, g_lm.name_unitid)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 居住专规用地编号
        create_new_field(lyr_PotentialLand, g_lm.name_landid, ogr.OFTInteger64)
        exec_str = r"UPDATE {} SET {}=ROWID".format(lyr_name_PotentialLand, g_lm.name_landid)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        log.info("计算职住系数...")
        # 1 职住系数
        create_new_field(lyr_Grid, g_lm.name_zzphxs, ogr.OFTReal)
        exec_str = r"UPDATE {} SET {}=CAST(({}+1) AS REAL)/({}+1)".format(lyr_name_Grid,
                                                                          g_lm.name_zzphxs, g_lm.name_CurJOB, g_lm.name_CurPop)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 2 创建 居住潜力用地_标准单元匹配 图层
        log.info('创建"居住潜力用地_标准单元匹配"图层')

        create_new_field(lyr_PotentialLand, g_lm.name_potentialLand_area, ogr.OFTReal)
        exec_str = r"UPDATE {} SET {}=CAST(st_area(GEOMETRY) as real)".format(lyr_name_PotentialLand,
                                                                              g_lm.name_potentialLand_area)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # geos的intesection算法会切出很多细碎的地块，可以考虑用st_area筛选一下
        # where st_ara(geometry) > 0.1
        exec_str = '''
            CREATE TABLE {} AS
                select * from (
                    SELECT CastToMultiPolygon(st_intersection(p.geometry, c.GEOMETRY)) AS geometry, p.*, c.* FROM {} AS c, {} AS p
                        WHERE st_intersects(p.geometry, c.geometry) = 1
                        AND c.ROWID IN (
                    SELECT ROWID
                        FROM SpatialIndex
                        WHERE f_table_name = '{}'
                        AND search_frame = p.geometry)) AS tlb_a where st_area(tlb_a.geometry) > 0.1
        '''.format(g_lm.name_layer_match, lyr_name_Grid, lyr_name_PotentialLand, lyr_name_Grid)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        srs = lyr_Grid.GetSpatialRef()
        srs_id = get_srs_id(srs)
        exec_str = '''SELECT RecoverGeometryColumn('{}', 'geometry', {}, "MULTIPOLYGON", "xy")'''.format(
            g_lm.name_layer_match, srs_id)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # output_lyr = CreateLayer(output_ds=dataSource, output_lyr_name=name_layer_match,
        #                          srs=srs1, geom_type=6, lco=["SPATIAL_INDEX=YES"],
        #                          input_lyr=lyr_PotentialLand, input_fields="ALL",
        #                          method_lyr=lyr_Grid, method_fields="ALL")
        #
        # if output_lyr is None:
        #     raise Exception('创建"{}"图层发生错误!'.format(name_layer_match))
        # else:
        #     lyr_PotentialLand.Intersection(lyr_Grid, output_lyr, options=["overwrite=YES", "PROMOTE_TO_MULTI=YES"])

        log.info('按面积比例更新"居住潜力用地_标准单元匹配"图层的字段'.format())

        # 3 按照切分后的面积比例重新计算r_po字段
        exec_str = r"UPDATE {} SET {}=CAST(st_area(GEOMETRY) as real) * {} / area".format(
            g_lm.name_layer_match, g_lm.name_r_po, g_lm.name_r_po)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 4 按照切分后的面积比例重新计算CurBldAdj字段
        # global name_CurBldAdj
        # name_CurBldAdj = vPotential_field["居住地块现状所有建筑面积"]
        exec_str = r"UPDATE {} SET {}=CAST(st_area(GEOMETRY) as real) * {} / area".format(
            g_lm.name_layer_match, g_lm.name_CurBldAdj, g_lm.name_CurBldAdj)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 5 按照切分后的面积比例重新计算CurRBld字段
        # global name_CurRBld
        # name_CurRBld = vPotential_field["居住地块现状居住建筑面积"]
        exec_str = r"UPDATE {} SET {}=CAST(st_area(GEOMETRY) as real) * {} / area".format(
            g_lm.name_layer_match, g_lm.name_CurRBld, g_lm.name_CurRBld)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 6 按照切分后的面积比例重新计算公共服务水平
        # name_publicService = vPotential_field["可享用的公服面积"]
        exec_str = r"UPDATE {} SET {}=CAST(st_area(GEOMETRY) as real) * {} / area".format(
            g_lm.name_layer_match, g_lm.name_PublicService, g_lm.name_PublicService)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 7 计算潜力用地面积
        log.info('计算"固定增加的居住建筑面积"...')
        create_new_field(lyr_Grid, g_lm.name_FixedAddRS, ogr.OFTReal)
        exec_str = '''UPDATE {} as c0 SET {}=tbl_a.R_PO_SUM from 
        (SELECT SUM({}-{}) AS R_PO_SUM, c.ROWID as rid from {} AS p LEFT OUTER JOIN {} AS c ON
            p.type <> 6 AND p.type <> 7 AND p.type <> 8 AND p.type <> 9  AND ST_Contains(c.geometry, st_centroid(p.geometry))
            AND c.ROWID in (
                SELECT ROWID FROM SpatialIndex WHERE f_table_name = '{}'
                    AND search_frame = st_centroid(p.geometry))
            GROUP BY rid
        ) AS tbl_a WHERE c0.ROWID=tbl_a.rid'''.format(lyr_name_Grid, g_lm.name_FixedAddRS, g_lm.name_r_po,
                                                      g_lm.name_CurRBld, g_lm.name_layer_match,
                                                      lyr_name_Grid, lyr_name_Grid)

        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        exec_str = '''UPDATE {} SET {}=0 where {} is null'''.format(
            lyr_name_Grid, g_lm.name_FixedAddRS, g_lm.name_FixedAddRS)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 8 计算固定增加的居住人口
        log.info('计算"固定增加的居住人口"...')

        create_new_field(lyr_Grid, g_lm.name_FixaddPOP, ogr.OFTInteger64)
        exec_str = '''UPDATE {} SET {}=round({}/35)'''.format(
            lyr_name_Grid, g_lm.name_FixaddPOP, g_lm.name_FixedAddRS)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 9 计算职住平衡分析权重
        log.info('计算"职住平衡分析权重"...')

        create_new_field(lyr_Grid, g_lm.name_weight, ogr.OFTReal)

        # CurPOP = vGrid_field["单元现状人口总数"]
        # CurJOB = vGrid_field["单元现状就业岗位总数"]
        exec_str = '''
            UPDATE {} as c0 SET {} = tlb_a.w FROM
                (SELECT cast(c1 - min(c1) OVER() as real) / (max(c1) OVER() - min(c1) OVER()) +
                    cast(c2 - min(c2) OVER() as real) / (max(c2) OVER() - min(c2) OVER()) as w
                    FROM 
                    (SELECT max({}, {}) AS c1, 
                        ( CASE 
                            WHEN {} < 1 THEN CAST(1/{} AS REAL)
                            WHEN {} >= 1 THEN {} END 
                        ) AS c2, rowid
                        from {} as c 
                    )
                ) as tlb_a where c0.rowid = tlb_a.rowid        
        '''.format(lyr_name_Grid, g_lm.name_weight, g_lm.name_CurPop, g_lm.name_CurJOB, g_lm.name_zzphxs,
                   g_lm.name_zzphxs, g_lm.name_zzphxs, g_lm.name_zzphxs,
                   lyr_name_Grid)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)
    finally:
        del exec_res
        del lyr_Grid
        del lyr_PotentialLand

def create_new_field(lyr, field_name, field_type, width=18, precision=10):
    index = lyr.FindFieldIndex(field_name, 0)
    if index > -1:
        lyr.DeleteField(index)

    new_field = ogr.FieldDefn(field_name, field_type)
    if field_type == ogr.OFTReal:
        new_field.SetWidth(width)
        new_field.SetPrecision(precision)
    elif field_type == ogr.OFTString:
        new_field.SetWidth(width)

    lyr.CreateField(new_field)
    del new_field


def create_temp_sqliteDB_by_qgis(layer, output_file, layer_name, bOpen=False):
    save_options = None
    save_options = QgsVectorFileWriter.SaveVectorOptions()
    save_options.driverName = 'SQLite'
    save_options.layerName = layer_name
    save_options.datasourceOptions = ["SPATIALITE=YES"]
    save_options.layerOptions = ["SPATIAL_INDEX=YES", "FID=OGC_FID"]
    save_options.geometryType = "PROMOTE_TO_MULTI"
    save_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer  # Update mode
    save_options.EditionCapability = QgsVectorFileWriter.CanAddNewLayer
    transform_context = QgsProject.instance().transformContext()

    error = QgsVectorFileWriter.writeAsVectorFormatV3(layer,
                                                      output_file,
                                                      transform_context,
                                                      save_options)

    if error[0] != QgsVectorFileWriter.NoError:
        save_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile  # Create mode

        error = QgsVectorFileWriter.writeAsVectorFormatV3(layer,
                                                          output_file,
                                                          transform_context,
                                                          save_options)

    if error[0] != QgsVectorFileWriter.NoError:
        raise Exception("创建临时数据库出错!错误原因:\n{}".format(traceback.format_exc()))

    if bOpen:
        wks = workspaceFactory().get_factory(DataType.sqlite)
        dataSource = wks.openFromFile(output_file + '.sqlite', 1)
        return dataSource
    else:
        return None


# 创建用于统计的临时数据库
def create_temp_sqliteDB(temp_sqliteDB_path, temp_sqliteDB_name, in_path, layer_name, bOpen=False):
    dataSource = None
    if not os.path.exists(temp_sqliteDB_path):
        os.mkdir(temp_sqliteDB_path)

    gdal.SetConfigOption("SHAPE_ENCODING", "GBK")
    if not os.path.exists(os.path.join(temp_sqliteDB_path, temp_sqliteDB_name)):
        translateOptions = gdal.VectorTranslateOptions(format="SQLite", layerName=layer_name,
                                                       datasetCreationOptions=["SPATIALITE=YES"],
                                                       layerCreationOptions=["SPATIAL_INDEX=YES"],
                                                       geometryType="PROMOTE_TO_MULTI")
    else:
        translateOptions = gdal.VectorTranslateOptions(format="SQLite", accessMode="update", layerName=layer_name,
                                                       layerCreationOptions=["SPATIAL_INDEX=YES"],
                                                       geometryType="PROMOTE_TO_MULTI")

    hr = gdal.VectorTranslate(os.path.join(temp_sqliteDB_path, temp_sqliteDB_name), in_path,
                              options=translateOptions)
    if not hr:
        raise Exception("创建临时数据库出错!错误原因:\n{}".format(traceback.format_exc()))
    else:
        del hr
        if bOpen:
            wks = workspaceFactory().get_factory(DataType.sqlite)
            dataSource = wks.openFromFile(os.path.join(temp_sqliteDB_path, temp_sqliteDB_name), 1)
            return dataSource
        else:
            return None


def remove_temp_sqliteDB(in_path, db_name):
    db_path = os.path.join(in_path, db_name)
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except:
        log.warning("删除临时sqlite数据库文件{}出错，可能是数据库文件被占用，请手动删除!".format(db_path))


def CreateLayer(
        output_ds,
        output_lyr_name,
        srs,
        geom_type=0,
        lco=[],
        input_lyr=None,
        input_fields="ALL",
        method_lyr=None,
        method_fields="ALL",
        opt=[],
):
    output_lyr = output_ds.CreateLayer(output_lyr_name, srs, geom_type, lco)
    if output_lyr is None:
        log.error('Cannot create layer "%s"' % output_lyr_name)
        return None

    if input_fields == "ALL" and method_fields == "ALL":
        return output_lyr

    input_prefix = ""
    method_prefix = ""
    for val in opt:
        if val.lower().find("input_prefix=") == 0:
            input_prefix = val[len("input_prefix="):]
        elif val.lower().find("method_prefix=") == 0:
            method_prefix = val[len("method_prefix="):]

    if input_fields == "ALL":
        layer_defn = input_lyr.GetLayerDefn()
        for idx in range(layer_defn.GetFieldCount()):
            fld_defn = layer_defn.GetFieldDefn(idx)
            fld_defn = ogr.FieldDefn(
                input_prefix + fld_defn.GetName(), fld_defn.GetType()
            )
            if output_lyr.CreateField(fld_defn) != 0:
                log.error(
                    'Cannot create field "%s" in layer "%s"'
                    % (fld_defn.GetName(), output_lyr.GetName())
                )

    elif input_fields != "NONE":
        layer_defn = input_lyr.GetLayerDefn()
        for fld in input_fields:
            idx = layer_defn.GetFieldIndex(fld)
            if idx < 0:
                log.error(
                    'Cannot find field "%s" in layer "%s"' % (fld, layer_defn.GetName())
                )
                continue
            fld_defn = layer_defn.GetFieldDefn(idx)
            fld_defn = ogr.FieldDefn(
                input_prefix + fld_defn.GetName(), fld_defn.GetType()
            )
            if output_lyr.CreateField(fld_defn) != 0:
                log.error(
                    'Cannot create field "%s" in layer "%s"'
                    % (fld, output_lyr.GetName())
                )

    if method_fields == "ALL":
        layer_defn = method_lyr.GetLayerDefn()
        for idx in range(layer_defn.GetFieldCount()):
            fld_defn = layer_defn.GetFieldDefn(idx)
            fld_defn = ogr.FieldDefn(
                method_prefix + fld_defn.GetName(), fld_defn.GetType()
            )
            if output_lyr.CreateField(fld_defn) != 0:
                log.error(
                    'Cannot create field "%s" in layer "%s"'
                    % (fld_defn.GetName(), output_lyr.GetName())
                )

    elif method_fields != "NONE":
        layer_defn = method_lyr.GetLayerDefn()
        for fld in method_fields:
            idx = layer_defn.GetFieldIndex(fld)
            if idx < 0:
                log.error(
                    'Cannot find field "%s" in layer "%s"' % (fld, layer_defn.GetName())
                )
                continue
            fld_defn = layer_defn.GetFieldDefn(idx)
            fld_defn = ogr.FieldDefn(
                method_prefix + fld_defn.GetName(), fld_defn.GetType()
            )
            if output_lyr.CreateField(fld_defn) != 0:
                log.error(
                    'Cannot create field "%s" in layer "%s"'
                    % (fld, output_lyr.GetName())
                )

    return output_lyr
