import base64
import json
import math
import os
import re
import sys
import time
from enum import Enum


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
# srs_desc_dict = {
#     "深圳独立": SpatialReference.sz_Local,
#     "CGCS2000地理": SpatialReference.gcs_2000,
#     "CGCS2000投影": SpatialReference.pcs_2000,
#     "CGCS2000投影(包含带号)": SpatialReference.pcs_2000_zone,
#     "WGS84": SpatialReference.wgs84,
#     "百度地理": SpatialReference.bd09,
#     "高德地理": SpatialReference.gcj02,
#     "西安80地理": SpatialReference.gcs_xian80,
#     "西安80投影": SpatialReference.pcs_xian80,
#     "西安80投影(包含带号)": SpatialReference.pcs_xian80_zone
# }

# srs_list = ["深圳独立", "CGCS2000投影", "WGS84", "百度地理", "高德地理", "CGCS2000地理",
#             "CGCS2000投影(包含带号)", "西安80地理", "西安80投影", "西安80投影(包含带号)"]



