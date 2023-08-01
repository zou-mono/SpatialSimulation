from enum import Enum

main_path = ""


def get_main_path():
    return main_path


class modelRole:
    layerID = 11000
    modelID = 11001
    model = 11002
    solution = 11003


#  模型运算中涉及图层和字段设置
class model_layer_meta():
    name_zzphxs = "BI"  # 职住平衡系数字段名称
    name_FixedAddRS = "FixedAddRS"  # 固定增加的居住建筑
    name_potentialLand_area = "area"  # 潜力用地面积字段
    name_layer_match = "居住潜力用地_标准单元匹配"
    name_CurRBld = "CurRBld"  # 居住地块现状居住建筑面积
    name_FixaddPOP = "FixaddPOP"  # 固定增加的居住人口
    name_weight = "Weight"  # 职住平衡分析权重
    name_unitid = "UnitID"  # 标准单元编号
    name_landid = "LandID" # 居住专规用地编号
    name_layer_Grid = "标准单元"
    name_layer_PotentialLand = "居住专规潜力用地"
    name_type = "type"
    name_r_po = "r_po"
    name_io = "IO"
    name_plabi = "PBI"
    name_CurBldAdj = "CurBldAdj"
    name_MetroIF = "Metro_IF"
    name_PublicService = "pubservice"
    name_result_io = "land_io"
    name_result_plabi = "UnitID_PlaBI"
    name_bSingleCal = 'bSingleCal'  # 单目标是否计算字段
    name_indicator = 'Indicator' #  指标字段的名称


#  模型配置文件设置
class model_config_params():
    Potential_Constraint = 'Potential_Constraint'
    IndicatorWeight = 'IndicatorWeight'
    PresetPara = 'PresetPara.csv'
    config_path = r"config"
    param_file = r"params.xlsx"
    result_folder = "res"  # 输出结果文件的位置
    # result_libs = "result_libs"  # 存放模型运算结果的档案数据库
    Indicator_net = "NetIncRPo"  # 净增长变量名称
    Indicator_demo = "DemoBld"  # 拆除变量名称
    Indicator_acc = "Acc"  # 轨道覆盖变量名称
    Indicator_pubService = "PublicService"  # 公共服务名称
    Indicator_bi = "BI"  # 职住平衡名称
    Indicator_multi = "multiple"


indicator_translate_dict = {
    model_config_params.Indicator_net: "新增居住建筑量",
    model_config_params.Indicator_demo: "拆除总建筑量",
    model_config_params.Indicator_acc: "交通可达性",
    model_config_params.Indicator_pubService: "公共服务水平",
    model_config_params.Indicator_bi: "职住平衡",
}

# 控制模型weight的顺序， 对后续模型矩阵运算影响很大
# key是顺序，同时也是区分结果图层中io,plabi字段的序号
# 第三列表示是否可以参与单目标优化运算
Weight_neccessary = {
    model_config_params.Indicator_net: ['新增总居住建筑量', 0, True],
    model_config_params.Indicator_demo: ['拆除总建筑量', 1, True],
    model_config_params.Indicator_acc: ['交通可达性', 2, True],
    model_config_params.Indicator_pubService: ['公共服务水平', 3, True],
    model_config_params.Indicator_bi: ['职住平衡指数', 4, False]
}

# 控制模型的prop， key是用地type值
prop_neccessary = {
    6: '总城市更新计划用地',
    7: '总土地整备计划用地',
    8: '总旧住宅区改居住用地',
    9: '总旧工业区改居住用地'
}

land_type_dict = {
    6: "城市更新计划用地",
    7: "土地整备计划用地",
    8: "旧住宅区改居住用地",
    9: "旧工业区改居住用地",
    1: "已出让未建设居住用地",
    2: "已批城市更新规划居住用地",
    3: "已批土地整备规划居住用地",
    4: "已批棚户区规划居住用地",
    5: "法定图则规划居住用地",
    10: "详规一张图商改居住潜力",
    11: "详规一张图工改居住潜力",
    12: "详规一张图发展备用地转居住",
    13: "轨道交通",
    14: "交通服务场站",
    15: "规划取消水厂",
    16: "变电站",
    17: "消防站",
    18: "生态线内"
}


class Dock(Enum):
    left = 0
    right = 1
    up = 2
    down = 3


class Tools(Enum):
    pan = 0
    zoomIn = 1
    zoomOut = 2
    identifyFeature = 3


class SplitterState(Enum):
    collapsed = 0
    expanded = 1


#  dock窗口名称
class Window_titles():
    model = "优化传导模型"
    layer = "图层列表"
    logView = "日志"
    identifyResult = "要素查询结果"


class SpatialReference:
    sz_Local = 2435
    gcs_2000 = 4490
    pcs_2000 = 4547
    pcs_2000_zone = 4526
    wgs84 = 4326
    bd09 = -2
    gcj02 = -1
    gcs_xian80 = 4610
    pcs_xian80 = 2383
    pcs_xian80_zone = 2362
    pcs_hk80 = 2326
    web_mercator = 3857

    @staticmethod
    def lst():
        return [2435, 4490, 4547, 4526, 4326, -1, -2, 4610, 2383, 2362, 2326, 3857]


class DataType(Enum):
    shapefile = 0
    geojson = 1
    cad_dwg = 2
    fileGDB = 3
    csv = 4
    xlsx = 5
    dbf = 6
    memory = 7
    openFileGDB = 8
    sqlite = 9
    FGDBAPI = 10


DataType_dict = {
    DataType.shapefile: "ESRI Shapefile",
    DataType.geojson: "geojson",
    DataType.fileGDB: "FileGDB",
    DataType.cad_dwg: "CAD"
}


srs_dict = {
    SpatialReference.sz_Local: "深圳独立",
    SpatialReference.gcs_2000: "CGCS2000地理",
    SpatialReference.pcs_2000: "CGCS2000投影",
    SpatialReference.pcs_2000_zone: "CGCS2000投影(包含带号)",
    SpatialReference.wgs84: "WGS84",
    SpatialReference.bd09: "百度地理",
    SpatialReference.gcj02: "高德地理",
    SpatialReference.gcs_xian80: "西安80地理",
    SpatialReference.pcs_xian80: "西安80投影",
    SpatialReference.pcs_xian80_zone: "西安80投影(包含带号)",
    SpatialReference.pcs_hk80: "香港80",
    SpatialReference.web_mercator: "web墨卡托"
}


def singleton(cls):
    instances = {}

    def _singleton(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return _singleton



