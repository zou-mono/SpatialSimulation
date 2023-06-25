import os
import sys
import time
import traceback

from osgeo import gdal, ogr

from UICore.DataFactory import workspaceFactory
from UICore.Gv import DataType
from UICore.common import get_srs_id
from UICore.log4p import Log

from osgeo_utils.ogr_layer_algebra import main

name_zzphxs = "BI"  # 职住平衡系数字段名称
name_FixedAddRS = "FixedAddRS" # 固定增加的居住建筑
name_potentialLand_area = "area"  # 潜力用地面积字段
name_layer_match = "居住潜力用地_标准单元匹配"

log = Log(__name__)

def modelCal(path_Grid, path_PotentialLand, lyr_name_Grid, lyr_name_PotentialLand, vGrid_field, vPotential_field):
    wks = None
    datasource = None

    cur_path, filename = os.path.split(os.path.abspath(sys.argv[0]))
    temp_sqliteDB_name = '%s.db' % (time.strftime('%Y-%m-%d-%H-%M-%S'))
    temp_sqliteDB_path = os.path.join(cur_path, "tmp")

    try:
        create_temp_sqliteDB(temp_sqliteDB_path, temp_sqliteDB_name, path_Grid, lyr_name_Grid)
        datasource = create_temp_sqliteDB(temp_sqliteDB_path, temp_sqliteDB_name, path_PotentialLand, lyr_name_PotentialLand, bOpen=True)

        field_cal(datasource, lyr_name_Grid, vGrid_field, lyr_name_PotentialLand, vPotential_field)

        return True
    except Exception as err:
        log.error(traceback.format_exc())
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
        log.info("计算职住系数...")
        # 1 职住系数
        if lyr_Grid.FindFieldIndex(name_zzphxs, 0) < 0:
            new_field = ogr.FieldDefn(name_zzphxs, ogr.OFTReal)
            new_field.SetWidth(18)
            new_field.SetPrecision(10)
            lyr_Grid.CreateField(new_field)
            del new_field

        CurPOP = vGrid_field["单元现状人口总数"]
        CurJOB = vGrid_field["单元现状就业岗位总数"]
        exec_str = r"UPDATE {} SET {}=CAST(({}+1) AS REAL)/({}+1)".format(lyr_name_Grid, name_zzphxs, CurJOB, CurPOP)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 2 FixedAddRS

        # 计算潜力用地面积
        log.info("计算固定增加的居住建筑面积...")
        if lyr_PotentialLand.FindFieldIndex(name_potentialLand_area, 0) < 0:
            new_field = ogr.FieldDefn(name_potentialLand_area, ogr.OFTReal)
            new_field.SetWidth(18)
            new_field.SetPrecision(10)
            lyr_PotentialLand.CreateField(new_field)
            del new_field

        exec_str = r"UPDATE {} SET {}=CAST(st_area(GEOMETRY) as real)".format(lyr_name_PotentialLand, name_potentialLand_area)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        # 创建 居住潜力用地_标准单元匹配 图层
        exec_str = '''
            CREATE TABLE {} AS 
                SELECT CastToMultiPolygon(st_intersection(p.geometry, c.GEOMETRY)) AS geometry, p.*, c.* FROM {} AS c, {} AS p 
                    WHERE st_intersects(p.geometry, c.geometry) = 1 
                    AND c.ROWID IN (
                SELECT ROWID 
                    FROM SpatialIndex
                    WHERE f_table_name = '{}' 
                    AND search_frame = p.geometry)
        '''.format(name_layer_match, lyr_name_Grid, lyr_name_PotentialLand, lyr_name_Grid)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        srs = lyr_Grid.GetSpatialRef()
        srs_id = get_srs_id(srs)
        exec_str = '''SELECT RecoverGeometryColumn('{}', 'geometry', {}, "MULTIPOLYGON", "xy")'''.format(name_layer_match, srs_id)
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

        # 按照切分后的面积比例重新计算r_po字段
        r_po = vPotential_field["新建居住建筑潜力面积"]
        exec_str = r"UPDATE {} SET {}=CAST(st_area(GEOMETRY) as real) * {} / area".format(name_layer_match, r_po, r_po)
        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

        lyr_Grid = dataSource.GetLayer(lyr_name_Grid)
        if lyr_Grid.FindFieldIndex(name_FixedAddRS, 0) < 0:
            new_field = ogr.FieldDefn(name_FixedAddRS, ogr.OFTReal)
            new_field.SetWidth(18)
            new_field.SetPrecision(10)
            lyr_Grid.CreateField(new_field)
            del new_field

        exec_str = '''UPDATE {} as c SET {}=tbl_a.R_PO_SUM from 
        (SELECT SUM({}) AS R_PO_SUM, c.ROWID as rid from {} AS p LEFT OUTER JOIN {} AS c ON
            p.type <> 6 AND p.type <> 7 AND p.type <> 8 AND p.type <> 9  AND ST_Contains(c.geometry, st_centroid(p.geometry))
            AND c.ROWID in (
                SELECT ROWID FROM SpatialIndex WHERE f_table_name = '{}'
                    AND search_frame = st_centroid(p.geometry))
            GROUP BY rid
        ) AS tbl_a WHERE c.ROWID=tbl_a.rid'''.format(lyr_name_Grid, name_FixedAddRS, r_po, name_layer_match,
                                                     lyr_name_Grid, lyr_name_Grid)

        exec_res = dataSource.ExecuteSQL(exec_str)
        dataSource.ReleaseResultSet(exec_res)

    finally:
        del exec_res
        del lyr_Grid


# 创建用于统计的临时数据库
def create_temp_sqliteDB(temp_sqliteDB_path, temp_sqliteDB_name, in_path, layer_name, bOpen=False):
    dataSource = None
    if not os.path.exists(temp_sqliteDB_path):
        os.mkdir(temp_sqliteDB_path)

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
            input_prefix = val[len("input_prefix=") :]
        elif val.lower().find("method_prefix=") == 0:
            method_prefix = val[len("method_prefix=") :]

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