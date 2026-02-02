import os
import sys

module_path = os.path.abspath(os.path.join(os.getcwd()))
if module_path not in sys.path:
    sys.path.append(module_path)

from math import sqrt
import model
import config
from osgeo import ogr, osr
import util

def geo2proj(lng, lat, EPSG=4326):
    
    source = osr.SpatialReference()
    source.ImportFromEPSG(EPSG)
    
    target = osr.SpatialReference()
    target.ImportFromEPSG(2437)
    
    transform = osr.CoordinateTransformation(source, target)
    
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(lat, lng)
    
    point.Transform(transform)
    
    lat_prj, lng_prj = point.GetX(), point.GetY()
    
    return lng_prj, lat_prj


def get_flow_field_velocity(raw_paths, lng, lat):
    
    _lng = float(lng)
    _lat = float(lat)

    lng_prj = 0.0
    lat_prj = 0.0
    if _lng <= 180.0 and _lat <= 180.0:
        lng_prj, lat_prj = geo2proj(_lng, _lat)
    elif _lng > 10000000.0:
        lng_prj, lat_prj = geo2proj(_lng, _lat, 3857)
    else:
        lng_prj = _lng
        lat_prj = _lat

    min_distance = float('inf')
    us = []
    vs = []
    index = 0

    # 从第一个时间点中找到距离最近点的索引
    with open(os.path.join(config.DIR_RESOURCE, raw_paths[0]), 'r') as file:
        # 跳过前两行
        for _ in range(2):
            next(file)

        # 从第三行开始处理
        for line_index, line in enumerate(file, start=2):
            parts = line.split()
            # 提取坐标和数据
            coords = (float(parts[0]), float(parts[1]))
            distance = util.calculate_distance(lng_prj, lat_prj, coords[0], coords[1])
            # 检查是否是最近的坐标
            if distance < min_distance:
                min_distance = distance
                index = line_index
    
    # 遍历所有时间点，根据索引找到对应点，获取u,v
    for i in range(26):
        path = os.path.join(config.DIR_RESOURCE, raw_paths[i])
        with open(path, 'r') as file:
            # 跳过前两行
            for _ in range(2):
                next(file)

            # 从第三行开始处理
            for line_index, line in enumerate(file, start=2):
                if line_index == index:
                    parts = line.split()
                    us.append(float(parts[-2]))
                    vs.append(float(parts[-1]))


    return {
        "us": us,
        "vs": vs
    }
    
##########################################################################################

@model.model_status_controller_sync
def run_flow_field_velocity_mcr(mcr: model.ModelCaseReference):

    hydrodynamic_mcr = model.ModelCaseReference.open_case(mcr.request_json['case-id'])
    lng = mcr.request_json['lng']
    lat = mcr.request_json['lat']
    
    # raw_path = os.path.join(hydrodynamic_mcr.directory, 'result', 'raw')
    raw_paths = hydrodynamic_mcr.make_response()['raw-txts']

    result = get_flow_field_velocity(raw_paths, lng, lat)

    return {
        'case-id': mcr.id,
        'result': result
    }

@model.model_status_controller_sync
def run_flow_field_velocities_mcr(mcr: model.ModelCaseReference):

    hydrodynamic_mcr = model.ModelCaseReference.open_case(mcr.request_json['case-id'])
    sample_points = mcr.request_json['sample-points']
    
    # raw_path = os.path.join(hydrodynamic_mcr.directory, 'result', 'raw')
    raw_paths = hydrodynamic_mcr.make_response()['raw-txts']

    result = []
    for sample_point in sample_points:
        lng = sample_point['lng']
        lat = sample_point['lat']
        result.append(get_flow_field_velocity(raw_paths, lng, lat))

    return {
        'case-id': mcr.id,
        'result': result
    }
    
##########################################################################################

NAME = 'Flow-Field Velocity'

CATEGORY = 'Numerical Model'

CATEGORY_ALIAS = 'nm'
 
def PARSING(self, request_json: dict, model_path: str, other_dependent_ids: list[str]=[]):
    
    flow_field_velocity_mcr = model.ModelCaseReference.create(config.API_NM_FLOW_FIELD_VELOCITY, request_json, NAME, model_path, other_dependent_ids)
    
    return [flow_field_velocity_mcr]

def RESPONSING(self, core_mcr: model.ModelCaseReference, default_pre_mcrs: list[model.ModelCaseReference], other_pre_mcrs: list[model.ModelCaseReference]):
    
    return core_mcr.make_response({
                                    'case-id': 'TEMPLATE',
                                    'result': 'NONE'
                                })
    
##########################################################################################

if __name__ == '__main__':
    
    v1 = sys.argv[1]    # flow_field_velocity_mcr
    
    flow_field_velocity_mcr = model.ModelCaseReference.open_case(v1)
    
    if not "sample-points" in flow_field_velocity_mcr.request_json:
        run_flow_field_velocity_mcr(flow_field_velocity_mcr)
    else:
        run_flow_field_velocities_mcr(flow_field_velocity_mcr)