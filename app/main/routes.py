import os
import util
import json
import config
import zipfile
from app.main import bp
from werkzeug.utils import secure_filename
from flask import request, jsonify, abort, Response
from .controllers import handle_model_runner, api_handlers

######################################## Utils ########################################
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.APP_ALLOWED_EXTENSIONS

######################################## Error Handler ########################################

@bp.errorhandler(400)
def not_found(error):
    
    response = jsonify({
        'status': 400,
        'error': 'Bad Request',
        'message': error.description
    })
    return response, 400

@bp.errorhandler(404)
def not_found(error):
    
    response = jsonify({
        'status': 404,
        'error': 'Not Found',
        'message': error.description
    })
    return response, 404

######################################## API for Model Case ########################################

@bp.route(config.API_MC_STATUS, methods=[ 'GET' ])
def get_model_case_status():
    
    case_id = request.args.get('id', type=str)
    
    status, response = api_handlers[config.API_MC_STATUS](case_id)
    if status == 200:
        return response
    if status == 404:
        abort(404, description=response)

@bp.route(config.API_MC_RESULT, methods=[ 'GET' ])
def get_model_case_result():
    
    case_id = request.args.get('id', type=str)
    status, response = api_handlers[config.API_MC_RESULT](case_id)
    if status == 200:
        return response
    if status == 404:
        abort(404, description=response)
        
@bp.route(config.API_MC_ERROR, methods=[ 'GET' ])
def get_model_case_error():
    
    case_id = request.args.get('id', type=str)
    status, response = api_handlers[config.API_MC_ERROR](case_id)
    if status == 200:
        return response
    if status == 404:
        abort(404, description=response)

@bp.route(config.API_MC_PRE_ERROR_CASES, methods=[ 'GET' ])
def get_pre_error_cases():
    
    case_id = request.args.get('id', type=str)
    status, resposne = api_handlers[config.API_MC_PRE_ERROR_CASES](case_id)
    if status == 200:
        return resposne
    if status == 404:
        abort(404, description=resposne)

@bp.route(config.API_MC_DELETE, methods = [ 'DELETE' ])
def delete_model_case():
    
    case_id = request.args.get('id', type=str)
    status, response = api_handlers[config.API_MC_DELETE](case_id)
    
    if status == 200:
        return response
    if status == 404:
        abort(404, description=response)
        
@bp.route(config.API_MCS_STATUS, methods=[ 'POST' ])
def get_model_cases_status():
    
    status, response = api_handlers[config.API_MCS_STATUS](request.get_json())
    if status == 200:
        return response
    if status == 404:
        abort(404, description=response)

@bp.route(config.API_MCS_TIME, methods=[ 'GET' ])
def get_model_cases_call_time():
    
    response = api_handlers[config.API_MCS_TIME]()
    return response

@bp.route(config.API_MCS_SERIALIZATION, methods=[ 'POST' ])
def get_model_cases_serialization():
    
    status, response = api_handlers[config.API_MCS_SERIALIZATION](request.get_json())
    if status == 200:
        return response
    if status == 404:
        abort(404, description=response)

@bp.route(config.API_MCS_DELETE, methods = [ 'POST' ])
def delete_model_cases():
    
    status, response = api_handlers[config.API_MCS_DELETE](request.get_json())
    
    if status == 200:
        return response
    if status == 404:
        abort(404, description=response)

@bp.route(config.API_FS_RESOURCE_DELETE, methods = [ 'DELETE' ])
def delete_resource_directory():
    
    directory = request.args.get('directory', type=str)
    print(directory)
    status, response = api_handlers[config.API_FS_RESOURCE_DELETE](directory)
    
    if status == 200:
        return response
    if status == 404:
        abort(404, description=response)

######################################## API for File System ########################################

@bp.route(config.API_FS_RESULT_FILE, methods=[ 'GET' ])
def get_model_case_file():
    
    case_id = request.args.get('id', type=str)
    filename = request.args.get('name', type=str)
    status, response = api_handlers[config.API_FS_RESULT_FILE](case_id, filename)
    
    if status == 200:
        return Response(util.generate_large_file(response), 
                        mimetype='application/octet-stream',
                        headers={'Content-Disposition': f'attachment; filename={response}'})
    if status == 404:
        abort(404, description=response)

@bp.route(config.API_FS_RESOURCE_FILE, methods=[ 'GET' ])
def get_resource_file():
    
    name = request.args.get('name', type=str)
    status, response = api_handlers[config.API_FS_RESOURCE_FILE](name)
    
    if status == 200:
        return Response(util.generate_large_file(response), 
                        mimetype='application/octet-stream',
                        headers={'Content-Disposition': f'attachment; filename={response}'})
    if status == 404:
        abort(404, description=response)

@bp.route(config.API_FS_RESULT_ZIP, methods=[ 'GET' ])
def get_model_case_zip():
    
    case_id = request.args.get('id', type=str)
    status, response = api_handlers[config.API_FS_RESULT_ZIP](case_id)
    
    if status == 200:
        return Response(util.generate_large_file(response), 
                        mimetype='application/octet-stream',
                        headers={'Content-Disposition': f'attachment; filename={response}'})
    if status == 404:
        abort(404, description=response)

@bp.route(config.API_FS_RESOURCE_ZIP, methods=[ 'POST' ])
def upload_resource_zip():
    
    if 'json' not in request.form:
        abort(400, description='No JSON data provided')
    request_json = json.loads(request.form['json'])
    
    resource_path = os.path.join(config.DIR_RESOURCE, request_json['type'])
    if not resource_path:
        abort(400, description='No type specified')
    
    if not os.path.exists(resource_path):
        os.makedirs(resource_path, exist_ok=True)
    
    if 'file' not in request.files:
        abort(400, description='No file part')
        
    file = request.files['file']
    if file.filename == '':
        abort(400, description='No selected file')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        zip_path = os.path.join(resource_path, filename)
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(resource_path)
        
        os.remove(zip_path)
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(resource_path))
        
        return 'OK'
    else:
        abort(400, description='File type not allowed')

@bp.route(config.API_FS_RESOURCE_TIFF, methods=[ 'POST' ])
def upload_tiff():
    
    if 'json' not in request.form:
        abort(400, description='No JSON Data Provided')
    request_json = json.loads(request.form['json'])
    
    segment = request_json['segment']
    year = request_json['year']
    set = request_json['set']
    name = request_json['name']
    set_path = os.path.join(config.DIR_RESOURCE_TIFF, segment, year, set)
    
    if 'file' not in request.files:
        abort(400, description='No File Part Provided')
        
    file = request.files['file']
    if file.filename == '':
        abort(400, description='No Selected File')
    
    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()
        
        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))
        
        if os.path.exists(os.path.join(file_path, name + '.tiff')):
            tiff_extension = 'tiff'
        elif os.path.exists(os.path.join(file_path, name + '.tif')):
            tiff_extension = 'tif'
        else:
            abort(400, description='Files Provided Are Incomplete')
            
        return {
            'directory': f'tiff/{segment}/{year}/{set}/{fn}/{name}.{tiff_extension}'
        }
    else:
        abort(400, description='File Type Not Allowed')

@bp.route(config.API_FS_RESOURCE_ADF, methods=[ 'POST' ])
def upload_adf():
    
    if 'json' not in request.form:
        abort(400, description='No JSON Data Provided')
    request_json = json.loads(request.form['json'])
    
    segment = request_json['segment']
    year = request_json['year']
    set = request_json['set']
    name = request_json['name']
    set_path = os.path.join(config.DIR_RESOURCE_ADF, segment, year, set)
    
    if 'file' not in request.files:
        abort(400, description='No File Part Provided')
        
    file = request.files['file']
    if file.filename == '':
        abort(400, description='No Selected File')
    
    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()
        
        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        adf_path = os.path.join(file_path, name + '.adf')
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))
        
        complete = True
        if not os.path.exists(adf_path):
            complete = False
        if not complete:
            abort(400, description='Files Provided Are Incomplete')
            
        return {
            'directory': f'adf/{segment}/{year}/{set}/{fn}/{name}.adf'
        }
    else:
        abort(400, description='File Type Not Allowed')

@bp.route(config.API_FS_RESOURCE_JSON, methods=[ 'POST' ])
def upload_json():
    
    if 'json' not in request.form:
        abort(400, description='No JSON Data Provided')
    request_json = json.loads(request.form['json'])
    
    segment = request_json['segment']
    year = request_json['year']
    set = request_json['set']
    name = request_json['name']
    set_path = os.path.join(config.DIR_RESOURCE_JSON, segment, year, set)
    
    if 'file' not in request.files:
        abort(400, description='No File Part Provided')
        
    file = request.files['file']
    if file.filename == '':
        abort(400, description='No Selected File')
    
    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()
        
        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        json_path = os.path.join(file_path, name + '.json')
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))
        
        complete = True
        if not os.path.exists(json_path):
            complete = False
        if not complete:
            abort(400, description='Files Provided Are Incomplete')
            
        return {
            'directory': f'json/{segment}/{year}/{set}/{fn}/{name}.json'
        }
    else:
        abort(400, description='File Type Not Allowed')

@bp.route(config.API_FS_RESOURCE_GEOJSON, methods=[ 'POST' ])
def upload_geojson():
    
    if 'json' not in request.form:
        abort(400, description='No JSON Data Provided')
    request_json = json.loads(request.form['json'])
    
    segment = request_json['segment']
    year = request_json['year']
    set = request_json['set']
    name = request_json['name']
    set_path = os.path.join(config.DIR_RESOURCE_GEOJSON, segment, year, set)
    
    if 'file' not in request.files:
        abort(400, description='No File Part Provided')
        
    file = request.files['file']
    if file.filename == '':
        abort(400, description='No Selected File')
    
    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()
        
        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        json_path = os.path.join(file_path, name + '.geojson')
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))
        
        complete = True
        if not os.path.exists(json_path):
            complete = False
        if not complete:
            abort(400, description='Files Provided Are Incomplete')
            
        return {
            'directory': f'geojson/{segment}/{year}/{set}/{fn}/{name}.geojson'
        }
    else:
        abort(400, description='File Type Not Allowed')

@bp.route(config.API_FS_RESOURCE_SHP, methods=[ 'POST' ])
def upload_shapefile():
    
    if 'json' not in request.form:
        abort(400, description='No JSON Data Provided')
    request_json = json.loads(request.form['json'])
    
    segment = request_json['segment']
    year = request_json['year']
    set = request_json['set']
    name = request_json['name']
    set_path = os.path.join(config.DIR_RESOURCE_SHP, segment, year, set)
    
    if 'file' not in request.files:
        abort(400, description='No File Part Provided')
        
    file = request.files['file']
    if file.filename == '':
        abort(400, description='No Selected File')
    
    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()
        
        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        shp_path = os.path.join(file_path, name + '.shp')
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))
        
        complete = True
        if not util.contains_extension(file_path, '.shp'):
            complete = False
        if not util.contains_extension(file_path, '.shx'):
            complete = False
        if not util.contains_extension(file_path, '.prj'):
            complete = False
        if not util.contains_extension(file_path, '.dbf'):
            complete = False
        if not os.path.exists(shp_path):
            complete = False
        if not complete:
            abort(400, description='Files Provided Are Incomplete')
            
        return {
            'directory': f'shp/{segment}/{year}/{set}/{fn}/{name}.shp'
        }
    else:
        abort(400, description='File Type Not Allowed')

@bp.route(config.API_FS_RESOURCE_HYDRODYNAMIC, methods=[ 'POST' ])
def upload_hydrodynamic_zip():
    
    if 'json' not in request.form:
        abort(400, description='No JSON Data Provided')
    request_json = json.loads(request.form['json'])
    
    segment = request_json['segment']
    year = request_json['year']
    set = request_json['set']
    boundary_path = request_json['boundary']
    set_path = os.path.join(config.DIR_RESOURCE_HYDRODYNAMIC, segment, year, set)
    
    if 'file' not in request.files:
        abort(400, description='No File Part Provided')
        
    file = request.files['file']
    if file.filename == '':
        abort(400, description='No Selected File')
    
    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        fn, fe = os.path.splitext(filename)
        zip_path = os.path.join(set_path, filename)
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()
        
        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        
        complete = True
        if not util.contains_extension(file_path, '.63'):
            complete = False
        if not util.contains_extension(file_path, '.64'):
            complete = False
        if not util.contains_extension(file_path, '.14'):
            complete = False
        if not complete:
            abort(400, description='Files Provided Are Incomplete')
            
        status = api_handlers[config.API_FS_RESOURCE_HYDRODYNAMIC](
            request_json['segment'],
            request_json['year'],
            request_json['set'],
            fn,
            request_json['temp'],
            boundary_path
        )
        if status == 200:
            return {
                'directory': f'hydrodynamic/{segment}/{year}/{set}/{fn}/'
            }
    else:
        abort(400, description='File Type Not Allowed')

@bp.route(config.API_FS_DISK_USAGE, methods=[ 'GET' ])
def get_disk_usage():
    
    return api_handlers[config.API_FS_DISK_USAGE]()

@bp.route(config.API_FS_RESOURCE_HYDRODYNAMIC_LIST, methods=[ 'GET' ])
def get_hydrodynamic_resource_list():
    
    return api_handlers[config.API_FS_RESOURCE_HYDRODYNAMIC_LIST]()

######################################## API for Models ########################################

@bp.route(config.API_MR, methods=[ 'GET', 'POST' ])
def set_model_runner(category: str, model_name: str):
    
    if request.method == 'GET':
        status, response = handle_model_runner(f'{config.API_VERSION}/{category}/{model_name}', request.args.to_dict())
    elif request.method == 'POST':
        if len(request.files) == 0:
            request_json = request.get_json()
        else:
            form_json = json.loads(request.form['json'])
            request_json = form_json
            request_json.update(request.files.to_dict())
        # request_json = request.get_json() if len(request.files) == 0 else dict(json.loads(request.form['json'])).update(request.files.to_dict())
        status, response = handle_model_runner(f'{config.API_VERSION}/{category}/{model_name}', request_json)
        
    if status == 200:
        return response


if __name__ == '__main__':

    print("--------------------------------------")
    bp.run(host='0.0.0.0', port=config.APP_PORT, debug=config.APP_DEBUG)
