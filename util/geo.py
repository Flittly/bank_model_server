import os
import json
from osgeo import ogr, osr

def convert_shp_to_geojson(shp_path, geojson_path):
    
    ogr.RegisterAll()

    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_data_source = shp_driver.Open(shp_path)  # 0 read-only

    if shp_data_source is None:
        print(f'Failed to open {shp_path}', flush=True)
        return

    # Get first layer
    shp_layer = shp_data_source.GetLayer()

    # Create geojson
    geojson_driver = ogr.GetDriverByName('GeoJSON')
    if os.path.exists(geojson_path):
        geojson_driver.DeleteDataSource(geojson_path)
    
    geojson_data_source = geojson_driver.CreateDataSource(geojson_path)
    if geojson_data_source is None:
        print(f'Failed to create {geojson_path}', flush=True)
        return

    # Define the WGS84 coordinate system
    wgs84_srs = osr.SpatialReference()
    wgs84_srs.ImportFromEPSG(4326)

    # Create the GeoJSON layer with WGS84 coordinate system
    geojson_layer = geojson_data_source.CreateLayer(
        shp_layer.GetName(), srs=wgs84_srs, geom_type=shp_layer.GetGeomType()
    )
    
    # Get the layer definition from the Shapefile
    shp_layer_defn = shp_layer.GetLayerDefn()
    
    # Create fields in the GeoJSON layer
    for i in range(shp_layer_defn.GetFieldCount()):
        field_defn = shp_layer_defn.GetFieldDefn(i)
        geojson_layer.CreateField(field_defn)

    # Create a coordinate transformation
    source_srs = shp_layer.GetSpatialRef()
    coord_trans = osr.CoordinateTransformation(source_srs, wgs84_srs)

    # Convert each feature
    for feature in shp_layer:
        geom = feature.GetGeometryRef()
        geom.Transform(coord_trans)  # Transform to WGS84
        feature.SetGeometry(geom)

        # Ensure correct coordinate order (longitude, latitude)
        geom_type = geom.GetGeometryType()
        if geom_type == ogr.wkbPoint:
            x, y = geom.GetX(), geom.GetY()
            geom.SetPoint(0, x, y)
        elif geom_type in [ogr.wkbLineString, ogr.wkbPolygon]:
            
            for ring in geom:
                for i in range(ring.GetPointCount()):
                    x, y = ring.GetPoint(i)[:2]
                    ring.SetPoint(i, x, y)

        geojson_layer.CreateFeature(feature)

    # Cleanup
    del shp_data_source
    del geojson_data_source
    
    # Correct geojson coords
    swap_coordinates(geojson_path)


def swap_coordinates(geojson_path):
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def swap_coords(coords):
        if isinstance(coords[0], list):
            return [swap_coords(coord) for coord in coords]
        else:
            return [coords[1], coords[0]]

    for feature in data['features']:
        geom_type = feature['geometry']['type']
        coords = feature['geometry']['coordinates']
        
        if geom_type == 'Point':
            feature['geometry']['coordinates'] = swap_coords(coords)
        elif geom_type in ['LineString', 'MultiPoint']:
            feature['geometry']['coordinates'] = [swap_coords(coord) for coord in coords]
        elif geom_type in ['Polygon', 'MultiLineString']:
            feature['geometry']['coordinates'] = [[swap_coords(coord) for coord in part] for part in coords]
        elif geom_type == 'MultiPolygon':
            feature['geometry']['coordinates'] = [[[swap_coords(coord) for coord in part] for part in polygon] for polygon in coords]
    
    with open(geojson_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_segment_lengths(geometry):
    
    segment_lengths = []
    
    for i in range(geometry.GetPointCount() - 1):
        pt1 = ogr.Geometry(ogr.wkbPoint)
        pt2 = ogr.Geometry(ogr.wkbPoint)
        pt1.AddPoint(*geometry.GetPoint(i))
        pt2.AddPoint(*geometry.GetPoint(i + 1))
        segment_length = pt1.Distance(pt2)
        segment_lengths.append(segment_length)
        
    return segment_lengths


def divide_line_string(geojson_data, num_points):
    
    # Get the line feature
    feature = geojson_data['features'][0]
    geometry = ogr.CreateGeometryFromJson(json.dumps(feature['geometry']))
    
    total_length = geometry.Length()
    step = total_length / (num_points - 1)
    points = [ geometry.GetPoint(0) ]
    
    segment_lengths = get_segment_lengths(geometry)
    current_distance = step
    count = 1
    
    if len(segment_lengths) == 0:
        raise SystemError('LineString Is Invalid')
    
    while count < num_points - 1:
        distance_covered = 0
        
        for j, segment_length in enumerate(segment_lengths):
            
            if distance_covered + segment_length >= current_distance:
                
                # Make the current segment
                pt1 = ogr.Geometry(ogr.wkbPoint)
                pt2 = ogr.Geometry(ogr.wkbPoint)
                pt1.AddPoint(*geometry.GetPoint(j))
                pt2.AddPoint(*geometry.GetPoint(j + 1))
                
                # Make new divided points
                ratio = (current_distance - distance_covered) / segment_length
                new_x = pt1.GetX() + ratio * (pt2.GetX() - pt1.GetX())
                new_y = pt1.GetY() + ratio * (pt2.GetY() - pt1.GetY())
                points.append((new_x, new_y))
                
                current_distance += step
                count += 1
                break
            distance_covered += segment_length

    points.append(geometry.GetPoint(geometry.GetPointCount() - 1))
    return points, step


def divide_point_line(input_points, num_points, WKT, end_index=None):
    
    if end_index == None or end_index >= len(input_points):
        end_index = len(input_points) - 1
    
    geometry = ogr.Geometry(ogr.wkbLineString)
    for i in range(end_index + 1):
        point = input_points[i]
        x, y = point[0], point[1]
        geometry.AddPoint_2D(x, y)
        
    srs = osr.SpatialReference()
    srs.ImportFromWkt(WKT)
    geometry.AssignSpatialReference(srs)
    
    total_length = geometry.Length()
    step = total_length / (num_points - 1)
    points = [ geometry.GetPoint(0) ]
    ps = geometry.GetPointCount()
    
    segment_lengths = get_segment_lengths(geometry)
    current_distance = step
    count = 1
    
    if len(segment_lengths) == 0:
        raise SystemError('LineString Is Invalid')
    
    while count < num_points - 1:
        distance_covered = 0
        
        for j, segment_length in enumerate(segment_lengths):
            
            if distance_covered + segment_length >= current_distance:
                
                # Make the current segment
                pt1 = ogr.Geometry(ogr.wkbPoint)
                pt2 = ogr.Geometry(ogr.wkbPoint)
                pt1.AddPoint(*geometry.GetPoint(j))
                pt2.AddPoint(*geometry.GetPoint(j + 1))
                
                # Make new divided points
                ratio = (current_distance - distance_covered) / segment_length
                new_x = pt1.GetX() + ratio * (pt2.GetX() - pt1.GetX())
                new_y = pt1.GetY() + ratio * (pt2.GetY() - pt1.GetY())
                points.append((new_x, new_y))
                
                current_distance += step
                count += 1
                break
            distance_covered += segment_length

    points.append(geometry.GetPoint(geometry.GetPointCount() - 1))
    return points, step
    

def points_to_geojson(points):
    
    features = []
    for point in points:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [point[0], point[1]]
            },
            "properties": {}
        })
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return geojson


def calculate_distance(x1, y1, x2, y2, epsg_code=2437):
    
    source = osr.SpatialReference()
    source.ImportFromEPSG(epsg_code)
    
    point1 = ogr.Geometry(ogr.wkbPoint)
    point1.AddPoint(x1, y1)

    point2 = ogr.Geometry(ogr.wkbPoint)
    point2.AddPoint(x2, y2)

    point1.AssignSpatialReference(source)
    point2.AssignSpatialReference(source)

    distance = point1.Distance(point2)

    return distance

if __name__ == '__main__':
    
    import sys
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    if module_path not in sys.path:
        sys.path.append(module_path)
        
    import config
    
    input_path = os.path.join(config.DIR_RESOURCE, '..', 'geojson', 'test', 'section.geojson')
    output_path = os.path.join(config.DIR_RESOURCE, '..', 'geojson', 'test', 'output.geojson')
    
    with open(input_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
        
    points, step = divide_line_string(geojson_data, 55)
    
    n_points, n_step = divide_point_line(points, 23, 3857, 10)
    
    points_json = points_to_geojson(n_points)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(points_json, f, indent = 4)
    
    # PERFORMANCE TEST!
    import time
    num_runs = 10000
    start_time = time.time()

    for _ in range(num_runs):
        equidistant_points = divide_line_string(geojson_data, 11)

    end_time = time.time()
    average_time = (end_time - start_time) / num_runs

    print(f"Average execution time over {num_runs} runs: {average_time:.6f} seconds", flush=True)
 
