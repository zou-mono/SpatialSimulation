import csv
import os
import traceback

from openpyxl import load_workbook
from osgeo import ogr, osr

from UICore import fgdb, filegdbapi
from UICore.common import launderName, is_header, check_encoding, read_first_line
from UICore.log4p import Log
from UICore.Gv import DataType

log = Log(__name__)


class workspaceFactory(object):
    def __init__(self):
        self.datasource = None
        self.driver = None
        self.driverName = ""

    def get_factory(self, factory):
        wks = None
        if factory == DataType.shapefile or factory == DataType.dbf:
            wks = shapefileWorkspaceFactory()
        elif factory == DataType.geojson:
            wks = geojsonWorkspaceFactory()
        elif factory == DataType.fileGDB:
            wks = filegdbWorkspaceFactory()
        elif factory == DataType.cad_dwg:
            wks = dwgWorkspaceFactory()
        elif factory == DataType.openFileGDB:
            wks = openfilegdbWorkspaceFactory()
        elif factory == DataType.sqlite:
            wks = sqliteWorkspaceFactory()
        elif factory == DataType.FGDBAPI:
            wks = fgdbapiWorkspaceFactory()

        if wks is None:
            log.error("不支持的空间数据格式!")

        return wks

    def openFromFile(self, file, access=0):
        if self.driver is None:
            log.error("缺失图形文件引擎{}!".format(self.driverName))
            return None
        else:
            try:
                if self.driver == "fgdbapi":
                    gdb = fgdb.GeoDatabase()
                    bflag, err_msg = gdb.Open(file)
                    if not bflag:
                        raise Exception(err_msg)
                    else:
                        self.datasource = gdb
                else:
                    self.datasource = self.driver.Open(file, access)
                return self.datasource
            except Exception as e:
                if self.driver == "fgdbapi":
                    log.error("打开文件{}发生错误!\n{}".format(file, e))
                else:
                    log.error("打开文件{}发生错误!\n{}".format(file, traceback.format_exc()))
                return None

    def openLayer(self, name):
        if self.datasource is not None:
            try:
                layer = self.datasource.GetLayer(name)
                if layer is None:
                    log.warning("图层{}不存在!".format(name))
                    return None
                else:
                    return layer
            except:
                log.error("读取图层{}发生错误!\n{}".format(name, traceback.format_exc()))
                return None

    def getLayers(self):
        layers = []
        if self.datasource is not None:
            for layer_idx in range(self.datasource.GetLayerCount()):
                layer = self.datasource.GetLayerByIndex(layer_idx)
                layers.append(layer)
            return layers
        else:
            return []

    def getLayerNames(self):
        layer_names = []
        if self.datasource is not None:
            for layer_idx in range(self.datasource.GetLayerCount()):
                layer = self.datasource.GetLayerByIndex(layer_idx)
                layer_names.append(layer.GetName())
            return layer_names
        else:
            return []

    def cloneLayer(self, in_layer, output_path, out_layer_name, out_srs, out_format):
        if self.driver is None:
            return None

        out_DS = None
        out_layer = None
        try:
            in_defn = in_layer.GetLayerDefn()

            if os.path.exists(output_path):
                # log.info("datasource已存在，在已有datasource基础上创建图层.")

                if out_format == DataType.shapefile or out_format == DataType.geojson:
                    self.driver.DeleteDataSource(output_path)

                    # 如果无法删除则再修改图层名新建一个
                    if os.path.exists(output_path):
                        output_path = launderName(output_path)
                        out_layer_name, suffix = os.path.splitext(os.path.basename(output_path))
                    out_DS = self.driver.CreateDataSource(output_path)
                elif out_format == DataType.fileGDB:
                    out_DS = self.openFromFile(output_path)
                    # out_layer = out_DS.GetLayer(out_layer_name)
                    # print(out_DS.TestCapability(ogr.ODsCDeleteLayer))
                    # if out_layer is not None:
                    #     out_DS.DeleteLayer(out_layer_name)
            else:
                out_DS = self.driver.CreateDataSource(output_path)

            srs = osr.SpatialReference()
            srs.ImportFromEPSG(out_srs)

            if out_format == DataType.shapefile:
                encode_name = in_layer.GetMetadataItem("SOURCE_ENCODING", "SHAPEFILE")
                if encode_name is None:
                    encode_name = in_layer.GetMetadataItem("ENCODING_FROM_LDID", "SHAPEFILE")
                    if encode_name is None:
                        encode_name = in_layer.GetMetadataItem("ENCODING_FROM_CPG", "SHAPEFILE")

                if encode_name is not None:
                    out_layer = out_DS.CreateLayer(out_layer_name, srs=srs, geom_type=in_layer.GetGeomType(),
                                                   options=['ENCODING={}'.format(encode_name)])
            elif out_format == DataType.fileGDB or out_format == DataType.geojson:
                out_layer = out_DS.CreateLayer(out_layer_name, srs=srs, geom_type=in_layer.GetGeomType())

            if out_layer is None:
                raise Exception("创建图层失败.")

            # out_layer.CreateField(in_defn)
            for i in range(in_defn.GetFieldCount()):
                fieldName = in_defn.GetFieldDefn(i).GetName()
                fieldTypeCode = in_defn.GetFieldDefn(i).GetType()
                new_field = ogr.FieldDefn(fieldName, fieldTypeCode)
                out_layer.CreateField(new_field)

            return output_path, out_layer.GetName()
        except Exception as e:
            log.error("{}\n{}".format(e, traceback.format_exc()))
            return None, None
        finally:
            out_DS = None
            out_layer = None

class fgdbapiWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        self.driver = "fgdbapi"

class shapefileWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        self.driverName = "ESRI Shapefile"
        self.driver = ogr.GetDriverByName(self.driverName)


class geojsonWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        self.driverName = "GeoJSON"
        self.driver = ogr.GetDriverByName(self.driverName)


class filegdbWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        self.driverName = "FileGDB"
        self.driver = ogr.GetDriverByName(self.driverName)


class openfilegdbWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        self.driverName = "OpenFileGDB"
        self.driver = ogr.GetDriverByName(self.driverName)


class dwgWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        self.driverName = "CAD"
        self.driver = ogr.GetDriverByName(self.driverName)


class sqliteWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        self.driverName = "SQLite"
        self.driver = ogr.GetDriverByName(self.driverName)


def read_table_header(file, format, supplyment=True, sheet=None):
    if format == DataType.csv:
        encoding = check_encoding(file)

        # with open(file, 'r', newline='', encoding=encoding) as f:
        #     reader = csv.reader(f)
        #     header = next(reader)  # gets the first line
        header = read_first_line(file, format, encoding=encoding)
        bheader = is_header(header)
        if not bheader and supplyment:
            header_list = []
            for i in range(len(header)):
                header_list.append("F{}".format(i))
            return header_list, encoding, bheader
        else:
            for i in range(len(header)):
                if header[i] == "" and supplyment:
                    header[i] = "F{}".format(i)
            return header, encoding, bheader
    elif format == DataType.dbf:
        wks = workspaceFactory().get_factory(DataType.dbf)
        datasource = wks.openFromFile(file)

        header_list = []
        if datasource is not None:
            in_layer = datasource.GetLayer()
            defn = in_layer.GetLayerDefn()
            for i in range(defn.GetFieldCount()):
                fieldName = defn.GetFieldDefn(i).GetName()
                # fieldTypeCode = defn.GetFieldDefn(i).GetType()
                # fieldType = defn.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
                # fieldWidth = defn.GetFieldDefn(i).GetWidth()
                # GetPrecision = defn.GetFieldDefn(i).GetPrecision()
                header_list.append(fieldName)
        return header_list
    elif format == DataType.xlsx:
        header = read_first_line(file, format, sheet=sheet)
        bheader = is_header(header)
        if not bheader and supplyment:
            header_list = []
            for i in range(len(header)):
                header_list.append("F{}".format(i))
            return header_list, bheader
        else:
            for i in range(len(header)):
                if header[i] == "" and supplyment:
                    header[i] = "F{}".format(i)

            return header, bheader
    elif format == DataType.memory:
        header = read_first_line(file, format, sheet=sheet)
        bheader = is_header(header)
        return header, bheader

def get_row_from_excel(ws, logicRow, columns):
    row = []
    for i in range(logicRow, columns + 1):
        cell_value = ws.cell(row=logicRow, column=i).value
        row.append(str(cell_value))
    return row


