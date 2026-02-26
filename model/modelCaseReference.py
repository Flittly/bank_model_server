import os
import sys
import time
import copy
import util
import json
import config
import datetime
import portalocker


######################################## Utils ########################################
        
def get_error_case_ids_in_log(case_id: str):
    
    error_log = ModelCaseReference.get_status_log(case_id)
    if error_log == None:
        return []
    
    return error_log.split('\n')[0].split('-')

######################################## Model Case Reference ########################################

class ModelCaseReference:
    
    def __init__(self, request_url: str, request_json: dict, model_name: str, model_path: str, dependent_case_ids: list[str] = []):
     
        with open(config.DIR_GLOBALE_FILE_LOCKER, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)

            self.model_name = model_name
            self.model_path = model_path
            self.request_url = request_url
            self.request_json = request_json
            self.id = util.generate_md5(request_url + json.dumps(request_json))
            self.directory = os.path.join(config.DIR_MODEL_CASE, self.id)
            self.local_file_locker = os.path.join(self.directory, 'lock')
            self.timestamp = int(0)
            self.dependencies = dependent_case_ids
                
            self.initialize()
            self.get_status()

            portalocker.unlock(lock_file)

    
    @staticmethod
    def create(request_url: str, request_json: dict, model_name: str, model_path: str, dependent_case_ids: list[str] = []):

        return ModelCaseReference(request_url, request_json, model_name, model_path, dependent_case_ids)
    
    def update_call_time(self):
    
        current_time = datetime.datetime.now()
        self.timestamp = int(current_time.timestamp() * 1000)
        old_timestamp =  int(util.get_filenames(os.path.join(self.directory, 'time'))[0])
        
        old_name = os.path.join(self.directory, 'time', f'{old_timestamp}')
        new_name = os.path.join(self.directory, 'time', f'{self.timestamp}')
        
        os.rename(old_name, new_name)
    
    def initialize(self):
        
        if os.path.exists(self.directory):
            return
        
        os.makedirs(self.directory)
     
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            os.mkdir(os.path.join(self.directory, 'time'))
            os.mkdir(os.path.join(self.directory, 'result'))
            os.mkdir(os.path.join(self.directory, 'status'))
                
            # Serialize request
            content = {
                'model': self.model_name,
                'model-path': self.model_path,
                'url': self.request_url,
                'json': self.request_json,
                'dependencies': self.dependencies,
            }
            with open(os.path.join(self.directory, 'identity.json'), 'w', encoding = 'utf-8') as file:
                json.dump(content, file, indent = 4)
            
            with open(os.path.join(self.directory, 'time', f'{self.timestamp}'), 'w', encoding = 'utf-8') as file:
                pass
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            portalocker.unlock(lock_file)
        
    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            self.save_to_database()

            portalocker.unlock(lock_file)
        
    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            # Save results to PostGIS database
            self.save_to_database()
            
            portalocker.unlock(lock_file)
    
    def save_to_database(self):
        """
        Parses the model results and saves them into the PostGIS database.
        
        Currently supports: Risk Level model.
        Reads 'result/risk_level.json' (or similar) and inserts into 'bank_risk_results' table.
        """
        try:
            import psycopg2
            
            # 1. 检查是否为风险等级计算模型 (Risk Level)
            if 'risk-level' not in self.request_url:
                return

            # 2. 这里的 result_json_path 是一个假设
            # 实际情况中，你需要告诉风险等级模型输出一个 summary.json 或者你解析现有的文件
            # 假设风险等级模型输出的结果里有一个 final_summary.json
            result_json_path = os.path.join(self.directory, 'result', 'final_summary.json') 
            
            # 如果没有找到特定的结果文件，可能直接从内存或者 response.json 读取
            # 这里为了演示，假设从 request_json 获取几何，从 result 获取分值
            risk_level = 0
            indicators = {}
            if os.path.exists(result_json_path):
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    risk_level = data.get('risk_level', 0)
                    indicators = data.get('indicators', {})

            # 3. 提取关键元数据 (Region, Segment Index)
            # 从请求参数中获取 segment (如 Mzs)
            region_code = self.request_json.get('segment', 'Unknown')
            # 从 section-geometry 中获取 index (如 6)
            geo_props = self.request_json.get('section-geometry', {}).get('properties', {})
            seg_idx = geo_props.get('index', 0)
            
            # 4. 构建标准命名 (Mzs_Seg006_202304_Risk)
            time_point = self.request_json.get('current-timepoint', '20000101').replace('-', '')
            segment_name = f"{region_code}_Seg{seg_idx:03d}_{time_point}_Risk"

            # 5. 连接数据库
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname=config.DB_NAME
            )
            cursor = conn.cursor()
            
            # 6. 准备几何数据 (GeoJSON -> PostGIS Geometry)
            geom_json_str = json.dumps(self.request_json['section-geometry']['geometry'])

            # 7. 执行插入
            insert_sql = """
            INSERT INTO bank_risk_results 
            (case_id, region_code, segment_index, segment_name, risk_level, indicators, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            ON CONFLICT (case_id) DO UPDATE 
            SET risk_level = EXCLUDED.risk_level, 
                indicators = EXCLUDED.indicators,
                run_time = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_sql, (
                self.id,
                region_code,
                seg_idx,
                segment_name,
                risk_level,
                json.dumps(indicators),
                geom_json_str
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully saved case {self.id} to database.")
            
        except Exception as e:
            print(f"Failed to save to database: {e}")

    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            # Save results to PostGIS database
            self.save_to_database()
            
            portalocker.unlock(lock_file)
    
    def save_to_database(self):
        """
        Parses the model results and saves them into the PostGIS database.
        
        Currently supports: Risk Level model.
        Reads 'result/risk_level.json' (or similar) and inserts into 'bank_risk_results' table.
        """
        try:
            import psycopg2
            
            # 1. 检查是否为风险等级计算模型 (Risk Level)
            if 'risk-level' not in self.request_url:
                return

            # 2. 这里的 result_json_path 是一个假设
            # 实际情况中，你需要告诉风险等级模型输出一个 summary.json 或者你解析现有的文件
            # 假设风险等级模型输出的结果里有一个 final_summary.json
            result_json_path = os.path.join(self.directory, 'result', 'final_summary.json') 
            
            # 如果没有找到特定的结果文件，可能直接从内存或者 response.json 读取
            # 这里为了演示，假设从 request_json 获取几何，从 result 获取分值
            risk_level = 0
            indicators = {}
            if os.path.exists(result_json_path):
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    risk_level = data.get('risk_level', 0)
                    indicators = data.get('indicators', {})

            # 3. 提取关键元数据 (Region, Segment Index)
            # 从请求参数中获取 segment (如 Mzs)
            region_code = self.request_json.get('segment', 'Unknown')
            # 从 section-geometry 中获取 index (如 6)
            geo_props = self.request_json.get('section-geometry', {}).get('properties', {})
            seg_idx = geo_props.get('index', 0)
            
            # 4. 构建标准命名 (Mzs_Seg006_202304_Risk)
            time_point = self.request_json.get('current-timepoint', '20000101').replace('-', '')
            segment_name = f"{region_code}_Seg{seg_idx:03d}_{time_point}_Risk"

            # 5. 连接数据库
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname=config.DB_NAME
            )
            cursor = conn.cursor()
            
            # 6. 准备几何数据 (GeoJSON -> PostGIS Geometry)
            geom_json_str = json.dumps(self.request_json['section-geometry']['geometry'])

            # 7. 执行插入
            insert_sql = """
            INSERT INTO bank_risk_results 
            (case_id, region_code, segment_index, segment_name, risk_level, indicators, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            ON CONFLICT (case_id) DO UPDATE 
            SET risk_level = EXCLUDED.risk_level, 
                indicators = EXCLUDED.indicators,
                run_time = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_sql, (
                self.id,
                region_code,
                seg_idx,
                segment_name,
                risk_level,
                json.dumps(indicators),
                geom_json_str
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully saved case {self.id} to database.")
            
        except Exception as e:
            print(f"Failed to save to database: {e}")

    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            # Save results to PostGIS database
            self.save_to_database()
            
            portalocker.unlock(lock_file)
    
    def save_to_database(self):
        """
        Parses the model results and saves them into the PostGIS database.
        
        Currently supports: Risk Level model.
        Reads 'result/risk_level.json' (or similar) and inserts into 'bank_risk_results' table.
        """
        try:
            import psycopg2
            
            # 1. 检查是否为风险等级计算模型 (Risk Level)
            if 'risk-level' not in self.request_url:
                return

            # 2. 这里的 result_json_path 是一个假设
            # 实际情况中，你需要告诉风险等级模型输出一个 summary.json 或者你解析现有的文件
            # 假设风险等级模型输出的结果里有一个 final_summary.json
            result_json_path = os.path.join(self.directory, 'result', 'final_summary.json') 
            
            # 如果没有找到特定的结果文件，可能直接从内存或者 response.json 读取
            # 这里为了演示，假设从 request_json 获取几何，从 result 获取分值
            risk_level = 0
            indicators = {}
            if os.path.exists(result_json_path):
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    risk_level = data.get('risk_level', 0)
                    indicators = data.get('indicators', {})

            # 3. 提取关键元数据 (Region, Segment Index)
            # 从请求参数中获取 segment (如 Mzs)
            region_code = self.request_json.get('segment', 'Unknown')
            # 从 section-geometry 中获取 index (如 6)
            geo_props = self.request_json.get('section-geometry', {}).get('properties', {})
            seg_idx = geo_props.get('index', 0)
            
            # 4. 构建标准命名 (Mzs_Seg006_202304_Risk)
            time_point = self.request_json.get('current-timepoint', '20000101').replace('-', '')
            segment_name = f"{region_code}_Seg{seg_idx:03d}_{time_point}_Risk"

            # 5. 连接数据库
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname=config.DB_NAME
            )
            cursor = conn.cursor()
            
            # 6. 准备几何数据 (GeoJSON -> PostGIS Geometry)
            geom_json_str = json.dumps(self.request_json['section-geometry']['geometry'])

            # 7. 执行插入
            insert_sql = """
            INSERT INTO bank_risk_results 
            (case_id, region_code, segment_index, segment_name, risk_level, indicators, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            ON CONFLICT (case_id) DO UPDATE 
            SET risk_level = EXCLUDED.risk_level, 
                indicators = EXCLUDED.indicators,
                run_time = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_sql, (
                self.id,
                region_code,
                seg_idx,
                segment_name,
                risk_level,
                json.dumps(indicators),
                geom_json_str
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully saved case {self.id} to database.")
            
        except Exception as e:
            print(f"Failed to save to database: {e}")

    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            # Save results to PostGIS database
            self.save_to_database()
            
            portalocker.unlock(lock_file)
    
    def save_to_database(self):
        """
        Parses the model results and saves them into the PostGIS database.
        
        Currently supports: Risk Level model.
        Reads 'result/risk_level.json' (or similar) and inserts into 'bank_risk_results' table.
        """
        try:
            import psycopg2
            
            # 1. 检查是否为风险等级计算模型 (Risk Level)
            if 'risk-level' not in self.request_url:
                return

            # 2. 这里的 result_json_path 是一个假设
            # 实际情况中，你需要告诉风险等级模型输出一个 summary.json 或者你解析现有的文件
            # 假设风险等级模型输出的结果里有一个 final_summary.json
            result_json_path = os.path.join(self.directory, 'result', 'final_summary.json') 
            
            # 如果没有找到特定的结果文件，可能直接从内存或者 response.json 读取
            # 这里为了演示，假设从 request_json 获取几何，从 result 获取分值
            risk_level = 0
            indicators = {}
            if os.path.exists(result_json_path):
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    risk_level = data.get('risk_level', 0)
                    indicators = data.get('indicators', {})

            # 3. 提取关键元数据 (Region, Segment Index)
            # 从请求参数中获取 segment (如 Mzs)
            region_code = self.request_json.get('segment', 'Unknown')
            # 从 section-geometry 中获取 index (如 6)
            geo_props = self.request_json.get('section-geometry', {}).get('properties', {})
            seg_idx = geo_props.get('index', 0)
            
            # 4. 构建标准命名 (Mzs_Seg006_202304_Risk)
            time_point = self.request_json.get('current-timepoint', '20000101').replace('-', '')
            segment_name = f"{region_code}_Seg{seg_idx:03d}_{time_point}_Risk"

            # 5. 连接数据库
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname=config.DB_NAME
            )
            cursor = conn.cursor()
            
            # 6. 准备几何数据 (GeoJSON -> PostGIS Geometry)
            geom_json_str = json.dumps(self.request_json['section-geometry']['geometry'])

            # 7. 执行插入
            insert_sql = """
            INSERT INTO bank_risk_results 
            (case_id, region_code, segment_index, segment_name, risk_level, indicators, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            ON CONFLICT (case_id) DO UPDATE 
            SET risk_level = EXCLUDED.risk_level, 
                indicators = EXCLUDED.indicators,
                run_time = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_sql, (
                self.id,
                region_code,
                seg_idx,
                segment_name,
                risk_level,
                json.dumps(indicators),
                geom_json_str
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully saved case {self.id} to database.")
            
        except Exception as e:
            print(f"Failed to save to database: {e}")

    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            # Save results to PostGIS database
            self.save_to_database()
            
            portalocker.unlock(lock_file)
    
    def save_to_database(self):
        """
        Parses the model results and saves them into the PostGIS database.
        
        Currently supports: Risk Level model.
        Reads 'result/risk_level.json' (or similar) and inserts into 'bank_risk_results' table.
        """
        try:
            import psycopg2
            
            # 1. 检查是否为风险等级计算模型 (Risk Level)
            if 'risk-level' not in self.request_url:
                return

            # 2. 这里的 result_json_path 是一个假设
            # 实际情况中，你需要告诉风险等级模型输出一个 summary.json 或者你解析现有的文件
            # 假设风险等级模型输出的结果里有一个 final_summary.json
            result_json_path = os.path.join(self.directory, 'result', 'final_summary.json') 
            
            # 如果没有找到特定的结果文件，可能直接从内存或者 response.json 读取
            # 这里为了演示，假设从 request_json 获取几何，从 result 获取分值
            risk_level = 0
            indicators = {}
            if os.path.exists(result_json_path):
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    risk_level = data.get('risk_level', 0)
                    indicators = data.get('indicators', {})

            # 3. 提取关键元数据 (Region, Segment Index)
            # 从请求参数中获取 segment (如 Mzs)
            region_code = self.request_json.get('segment', 'Unknown')
            # 从 section-geometry 中获取 index (如 6)
            geo_props = self.request_json.get('section-geometry', {}).get('properties', {})
            seg_idx = geo_props.get('index', 0)
            
            # 4. 构建标准命名 (Mzs_Seg006_202304_Risk)
            time_point = self.request_json.get('current-timepoint', '20000101').replace('-', '')
            segment_name = f"{region_code}_Seg{seg_idx:03d}_{time_point}_Risk"

            # 5. 连接数据库
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname=config.DB_NAME
            )
            cursor = conn.cursor()
            
            # 6. 准备几何数据 (GeoJSON -> PostGIS Geometry)
            geom_json_str = json.dumps(self.request_json['section-geometry']['geometry'])

            # 7. 执行插入
            insert_sql = """
            INSERT INTO bank_risk_results 
            (case_id, region_code, segment_index, segment_name, risk_level, indicators, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            ON CONFLICT (case_id) DO UPDATE 
            SET risk_level = EXCLUDED.risk_level, 
                indicators = EXCLUDED.indicators,
                run_time = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_sql, (
                self.id,
                region_code,
                seg_idx,
                segment_name,
                risk_level,
                json.dumps(indicators),
                geom_json_str
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully saved case {self.id} to database.")
            
        except Exception as e:
            print(f"Failed to save to database: {e}")

    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            # Save results to PostGIS database
            self.save_to_database()
            
            portalocker.unlock(lock_file)
    
    def save_to_database(self):
        """
        Parses the model results and saves them into the PostGIS database.
        
        Currently supports: Risk Level model.
        Reads 'result/risk_level.json' (or similar) and inserts into 'bank_risk_results' table.
        """
        try:
            import psycopg2
            
            # 1. 检查是否为风险等级计算模型 (Risk Level)
            if 'risk-level' not in self.request_url:
                return

            # 2. 这里的 result_json_path 是一个假设
            # 实际情况中，你需要告诉风险等级模型输出一个 summary.json 或者你解析现有的文件
            # 假设风险等级模型输出的结果里有一个 final_summary.json
            result_json_path = os.path.join(self.directory, 'result', 'final_summary.json') 
            
            # 如果没有找到特定的结果文件，可能直接从内存或者 response.json 读取
            # 这里为了演示，假设从 request_json 获取几何，从 result 获取分值
            risk_level = 0
            indicators = {}
            if os.path.exists(result_json_path):
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    risk_level = data.get('risk_level', 0)
                    indicators = data.get('indicators', {})

            # 3. 提取关键元数据 (Region, Segment Index)
            # 从请求参数中获取 segment (如 Mzs)
            region_code = self.request_json.get('segment', 'Unknown')
            # 从 section-geometry 中获取 index (如 6)
            geo_props = self.request_json.get('section-geometry', {}).get('properties', {})
            seg_idx = geo_props.get('index', 0)
            
            # 4. 构建标准命名 (Mzs_Seg006_202304_Risk)
            time_point = self.request_json.get('current-timepoint', '20000101').replace('-', '')
            segment_name = f"{region_code}_Seg{seg_idx:03d}_{time_point}_Risk"

            # 5. 连接数据库
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname=config.DB_NAME
            )
            cursor = conn.cursor()
            
            # 6. 准备几何数据 (GeoJSON -> PostGIS Geometry)
            geom_json_str = json.dumps(self.request_json['section-geometry']['geometry'])

            # 7. 执行插入
            insert_sql = """
            INSERT INTO bank_risk_results 
            (case_id, region_code, segment_index, segment_name, risk_level, indicators, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            ON CONFLICT (case_id) DO UPDATE 
            SET risk_level = EXCLUDED.risk_level, 
                indicators = EXCLUDED.indicators,
                run_time = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_sql, (
                self.id,
                region_code,
                seg_idx,
                segment_name,
                risk_level,
                json.dumps(indicators),
                geom_json_str
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully saved case {self.id} to database.")
            
        except Exception as e:
            print(f"Failed to save to database: {e}")

    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            # Save results to PostGIS database
            self.save_to_database()
            
            portalocker.unlock(lock_file)
    
    def save_to_database(self):
        """
        Parses the model results and saves them into the PostGIS database.
        
        Currently supports: Risk Level model.
        Reads 'result/risk_level.json' (or similar) and inserts into 'bank_risk_results' table.
        """
        try:
            import psycopg2
            
            # 1. 检查是否为风险等级计算模型 (Risk Level)
            if 'risk-level' not in self.request_url:
                return

            # 2. 这里的 result_json_path 是一个假设
            # 实际情况中，你需要告诉风险等级模型输出一个 summary.json 或者你解析现有的文件
            # 假设风险等级模型输出的结果里有一个 final_summary.json
            result_json_path = os.path.join(self.directory, 'result', 'final_summary.json') 
            
            # 如果没有找到特定的结果文件，可能直接从内存或者 response.json 读取
            # 这里为了演示，假设从 request_json 获取几何，从 result 获取分值
            risk_level = 0
            indicators = {}
            if os.path.exists(result_json_path):
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    risk_level = data.get('risk_level', 0)
                    indicators = data.get('indicators', {})

            # 3. 提取关键元数据 (Region, Segment Index)
            # 从请求参数中获取 segment (如 Mzs)
            region_code = self.request_json.get('segment', 'Unknown')
            # 从 section-geometry 中获取 index (如 6)
            geo_props = self.request_json.get('section-geometry', {}).get('properties', {})
            seg_idx = geo_props.get('index', 0)
            
            # 4. 构建标准命名 (Mzs_Seg006_202304_Risk)
            time_point = self.request_json.get('current-timepoint', '20000101').replace('-', '')
            segment_name = f"{region_code}_Seg{seg_idx:03d}_{time_point}_Risk"

            # 5. 连接数据库
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname=config.DB_NAME
            )
            cursor = conn.cursor()
            
            # 6. 准备几何数据 (GeoJSON -> PostGIS Geometry)
            geom_json_str = json.dumps(self.request_json['section-geometry']['geometry'])

            # 7. 执行插入
            insert_sql = """
            INSERT INTO bank_risk_results 
            (case_id, region_code, segment_index, segment_name, risk_level, indicators, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            ON CONFLICT (case_id) DO UPDATE 
            SET risk_level = EXCLUDED.risk_level, 
                indicators = EXCLUDED.indicators,
                run_time = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_sql, (
                self.id,
                region_code,
                seg_idx,
                segment_name,
                risk_level,
                json.dumps(indicators),
                geom_json_str
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully saved case {self.id} to database.")
            
        except Exception as e:
            print(f"Failed to save to database: {e}")

    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            # Save results to PostGIS database
            self.save_to_database()
            
            portalocker.unlock(lock_file)
    
    def save_to_database(self):
        """
        Parses the model results and saves them into the PostGIS database.
        
        Currently supports: Risk Level model.
        Reads 'result/risk_level.json' (or similar) and inserts into 'bank_risk_results' table.
        """
        try:
            import psycopg2
            
            # 1. 检查是否为风险等级计算模型 (Risk Level)
            if 'risk-level' not in self.request_url:
                return

            # 2. 这里的 result_json_path 是一个假设
            # 实际情况中，你需要告诉风险等级模型输出一个 summary.json 或者你解析现有的文件
            # 假设风险等级模型输出的结果里有一个 final_summary.json
            result_json_path = os.path.join(self.directory, 'result', 'final_summary.json') 
            
            # 如果没有找到特定的结果文件，可能直接从内存或者 response.json 读取
            # 这里为了演示，假设从 request_json 获取几何，从 result 获取分值
            risk_level = 0
            indicators = {}
            if os.path.exists(result_json_path):
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    risk_level = data.get('risk_level', 0)
                    indicators = data.get('indicators', {})

            # 3. 提取关键元数据 (Region, Segment Index)
            # 从请求参数中获取 segment (如 Mzs)
            region_code = self.request_json.get('segment', 'Unknown')
            # 从 section-geometry 中获取 index (如 6)
            geo_props = self.request_json.get('section-geometry', {}).get('properties', {})
            seg_idx = geo_props.get('index', 0)
            
            # 4. 构建标准命名 (Mzs_Seg006_202304_Risk)
            time_point = self.request_json.get('current-timepoint', '20000101').replace('-', '')
            segment_name = f"{region_code}_Seg{seg_idx:03d}_{time_point}_Risk"

            # 5. 连接数据库
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname=config.DB_NAME
            )
            cursor = conn.cursor()
            
            # 6. 准备几何数据 (GeoJSON -> PostGIS Geometry)
            geom_json_str = json.dumps(self.request_json['section-geometry']['geometry'])

            # 7. 执行插入
            insert_sql = """
            INSERT INTO bank_risk_results 
            (case_id, region_code, segment_index, segment_name, risk_level, indicators, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            ON CONFLICT (case_id) DO UPDATE 
            SET risk_level = EXCLUDED.risk_level, 
                indicators = EXCLUDED.indicators,
                run_time = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_sql, (
                self.id,
                region_code,
                seg_idx,
                segment_name,
                risk_level,
                json.dumps(indicators),
                geom_json_str
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully saved case {self.id} to database.")
            
        except Exception as e:
            print(f"Failed to save to database: {e}")

    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            self.save_to_database()

            portalocker.unlock(lock_file)
        
    def get_status(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            portalocker.unlock(lock_file)
            return self.status
    
    def update_status(self, status, content=None, mode = 'a'):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            if self.status == status:
                portalocker.unlock(lock_file)
                return
            
            old_name = os.path.join(self.directory, 'status', f'{self.status}')
            new_name = os.path.join(self.directory, 'status', f'{status}')
            self.status = status
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({self.model_name}: {self.id}) status to {status}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            self.update_call_time()
            
            with open(os.path.join(self.directory, 'status', f'{config.STATUS_UNLOCK}'), 'w', encoding = 'utf-8') as file:
                file.write('OK')
            
            with open(os.path.join(self.directory, 'response.json'), 'w', encoding = 'utf-8') as file:
                json.dump({
                    'model': self.model_name,
                    'case-id': self.id,
                }, file, indent = 4)
            
            self.update_call_time()
            
            # Save results to PostGIS database
            self.save_to_database()
            
            portalocker.unlock(lock_file)
    
    def save_to_database(self):
        """
        Parses the model results and saves them into the PostGIS database.
        
        Currently supports: Risk Level model.
        Reads 'result/risk_level.json' (or similar) and inserts into 'bank_risk_results' table.
        """
        try:
            import psycopg2
            
            # 1. 检查是否为风险等级计算模型 (Risk Level)
            if 'risk-level' not in self.request_url:
                return

            # 2. 这里的 result_json_path 是一个假设
            # 实际情况中，你需要告诉风险等级模型输出一个 summary.json 或者你解析现有的文件
            # 假设风险等级模型输出的结果里有一个 final_summary.json
            result_json_path = os.path.join(self.directory, 'result', 'final_summary.json') 
            
            # 如果没有找到特定的结果文件，可能直接从内存或者 response.json 读取
            # 这里为了演示，假设从 request_json 获取几何，从 result 获取分值
            risk_level = 0
            indicators = {}
            if os.path.exists(result_json_path):
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    risk_level = data.get('risk_level', 0)
                    indicators = data.get('indicators', {})

            # 3. 提取关键元数据 (Region, Segment Index)
            # 从请求参数中获取 segment (如 Mzs)
            region_code = self.request_json.get('segment', 'Unknown')
            # 从 section-geometry 中获取 index (如 6)
            geo_props = self.request_json.get('section-geometry', {}).get('properties', {})
            seg_idx = geo_props.get('index', 0)
            
            # 4. 构建标准命名 (Mzs_Seg006_202304_Risk)
            time_point = self.request_json.get('current-timepoint', '20000101').replace('-', '')
            segment_name = f"{region_code}_Seg{seg_idx:03d}_{time_point}_Risk"

            # 5. 连接数据库
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname=config.DB_NAME
            )
            cursor = conn.cursor()
            
            # 6. 准备几何数据 (GeoJSON -> PostGIS Geometry)
            geom_json_str = json.dumps(self.request_json['section-geometry']['geometry'])

            # 7. 执行插入
            insert_sql = """
            INSERT INTO bank_risk_results 
            (case_id, region_code, segment_index, segment_name, risk_level, indicators, geom)
            VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            ON CONFLICT (case_id) DO UPDATE 
            SET risk_level = EXCLUDED.risk_level, 
                indicators = EXCLUDED.indicators,
                run_time = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_sql, (
                self.id,
                region_code,
                seg_idx,
                segment_name,
                risk_level,
                json.dumps(indicators),
                geom_json_str
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Successfully saved case {self.id} to database.")
            
        except Exception as e:
            print(f"Failed to save to database: {e}")