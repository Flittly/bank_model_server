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
            portalocker.unlock(lock_file)
    
    def find_status(self, status):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            result = (self.status & status) == status
            
            portalocker.unlock(lock_file)
            return result
        
    def is_used(self): 
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            path = os.path.join(self.directory, 'status')
            filenames = util.get_filenames(path)
            self.status = int(filenames[0])
            
            is_completed = (self.status & config.STATUS_COMPLETE) == config.STATUS_COMPLETE
            is_error = (self.status & config.STATUS_ERROR) == config.STATUS_ERROR
            is_locked = (self.status & config.STATUS_LOCK) == config.STATUS_LOCK
            
            result = is_completed or is_error or is_locked
            portalocker.unlock(lock_file)
            return result
    
    def make_response(self, content=None):
        
        current_status = self.get_status()
        response_file_path = os.path.join(self.directory, 'response.json')
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
        
            if content is not None: 
                    
                content['case-id'] = self.id
                content['model'] = self.model_name
            
                with open(response_file_path, 'w', encoding = 'utf-8') as file:
                    json.dump(content, file, indent = 4)
                self.update_call_time()

                portalocker.unlock(lock_file)
                return content
            
            else:
                with open(response_file_path, 'r', encoding='utf-8') as file:
                    content = json.load(file)
                
                portalocker.unlock(lock_file)
                return content
    
    def result_packaging(self):
        
        with open(self.local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
        
            result_path = os.path.join(self.directory, 'result')
            zip_file = os.path.join(self.directory, 'result')
            
            util.create_zip_from_folder(result_path, zip_file)
            
            self.update_call_time()
            portalocker.unlock(lock_file)
        
        return zip_file + '.zip'
    
    @staticmethod
    def generate_pre_error_log(current_case_id, pre_case_ids: list[str]):
        
        error_log = ''
        for case_id in pre_case_ids:
            error_log += f'{case_id}-'
        error_log = error_log[:-1]
        
        error_log += f'\n\n========= Error before Model Case ({ModelCaseReference.get_model_name(current_case_id)}: {current_case_id}) =========\n\n'
        
        for case_id in pre_case_ids:
            
            error_log += f'Pre Model Case ({ModelCaseReference.get_model_name(case_id)}: {case_id}) ERROR\n\n'
            error_log += (ModelCaseReference.get_status_log(case_id) + '\n')
        
        return error_log
    
    @staticmethod
    def get_simplified_error_log(case_id: str):
        
        id_set = set()
        id_stack = util.Stack()
        
        # Initialize error-id stack
        for id in ModelCaseReference.get_case_dependencies(case_id):
            if ModelCaseReference.has_case(id) and ModelCaseReference.is_case_error(id):
                id_stack.push(id)
        
        # Stack recursion
        while not id_stack.is_empty():
            
            error_id = id_stack.pop()
            id_set.add(error_id)
            
            for id in ModelCaseReference.get_case_dependencies(error_id):
                if ModelCaseReference.has_case(id) and ModelCaseReference.is_case_error(id):
                    id_stack.push(id)
        
        error_log = ''
        for id in id_set:
            
            error_log += f'=== Error Happened When Model Case ({ModelCaseReference.get_model_name(id)}: {id}) Running ===\n{ModelCaseReference.get_status_log(id)}\n'

        return error_log
    
    @staticmethod
    def get_model_name(case_id: str):
        
        with open(os.path.join(config.DIR_MODEL_CASE, case_id, 'identity.json'), 'r', encoding='utf-8') as file:
            model_name = json.load(file)['model']
        return model_name
    
    @staticmethod
    def get_case_dependencies(case_id: str):
        
        with open(os.path.join(config.DIR_MODEL_CASE, case_id, 'identity.json'), 'r', encoding='utf-8') as file:
            dependencies = json.load(file)['dependencies']
        return dependencies
    
    @staticmethod
    def has_case(case_id: str):
        
        if os.path.exists(os.path.join(config.DIR_MODEL_CASE, case_id)): 
            return True
        return False
        
    @staticmethod
    def open_case(case_id: str):
        
        directory = os.path.join(config.DIR_MODEL_CASE, case_id)
        if not os.path.exists(directory):
            return None
        
        with open(os.path.join(directory, 'identity.json'), "r") as file:
            content = json.load(file)

        model_name = content['model']
        request_url = content['url']
        request_json = content['json']
        model_path = content['model-path']
        dependencies = content['dependencies']

        return ModelCaseReference.create(request_url, request_json, model_name, model_path, dependencies)
    
    @staticmethod
    def delete_case(case_id: str):
        
        with open(config.DIR_GLOBALE_FILE_LOCKER, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            directory = os.path.join(config.DIR_MODEL_CASE, case_id)
            util.update_size(config.DIR_STORAGE_LOG, -util.get_folder_size_in_gb(directory))
            
            if not os.path.exists(directory):
                portalocker.unlock(lock_file)
                return False
            
            util.delete_folder_contents(directory)
            portalocker.unlock(lock_file)
            return True
    
    @staticmethod
    def is_case_locked(case_id: str):

        path = os.path.join(config.DIR_MODEL_CASE, case_id, 'status')
        local_file_locker = os.path.join(config.DIR_MODEL_CASE, case_id, 'lock')
        if not os.path.exists(path):
            return None

        with open(local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            filenames = util.get_filenames(path)
            status_code = int(filenames[0])

            portalocker.unlock(lock_file)

        if (status_code & config.STATUS_LOCK) == config.STATUS_LOCK:
            return True
        return False
    
    @staticmethod
    def get_case_time(case_id: str):

        local_file_locker = os.path.join(config.DIR_MODEL_CASE, case_id, 'lock')
        with open(local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            time = int(util.get_filenames(os.path.join(config.DIR_MODEL_CASE, case_id, 'time'))[0])

            portalocker.unlock(lock_file)
        
        return time
    
    @staticmethod
    def get_case_status(case_id: str):

        local_file_locker = os.path.join(config.DIR_MODEL_CASE, case_id, 'lock')
        with open(local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            current_status = int(util.get_filenames(os.path.join(config.DIR_MODEL_CASE, case_id, 'status'))[0])
            
            portalocker.unlock(lock_file)
        
        return current_status

    @staticmethod
    def check_case_status(case_id: str):

        local_file_locker = os.path.join(config.DIR_MODEL_CASE, case_id, 'lock')
        with open(local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            current_status = int(util.get_filenames(os.path.join(config.DIR_MODEL_CASE, case_id, 'status'))[0])
            
            portalocker.unlock(lock_file)
        
        if (current_status & config.STATUS_COMPLETE) == config.STATUS_COMPLETE:
            return 'COMPLETE'
        if (current_status & config.STATUS_RUNNING) == config.STATUS_RUNNING:
            return 'RUNNING'
        if (current_status & config.STATUS_ERROR) == config.STATUS_ERROR:
            return 'ERROR'
        if (current_status & config.STATUS_NONE) == config.STATUS_NONE:
            return 'NONE'
        if (current_status & config.STATUS_UNLOCK) == config.STATUS_UNLOCK:
            return 'UNLOCK'
        if (current_status & config.STATUS_LOCK) == config.STATUS_LOCK:
            return 'LOCK'
    
    @staticmethod
    def get_case_response(case_id: str):

        response_file_path = os.path.join(config.DIR_MODEL_CASE, case_id, 'response.json')
        local_file_locker = os.path.join(config.DIR_MODEL_CASE, case_id, 'lock')
        with open(local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            with open(response_file_path, 'r', encoding='utf-8') as file:
                content = json.load(file)
            
            portalocker.unlock(lock_file)
        
        return content
    
    @staticmethod
    def get_status_log(case_id: str):
        
        if not os.path.exists(os.path.join(config.DIR_MODEL_CASE, case_id, 'status')):
            return None
        
        status_code = util.get_filenames(os.path.join(config.DIR_MODEL_CASE, case_id, 'status'))[0]
        with open(os.path.join(config.DIR_MODEL_CASE, case_id, 'status', status_code), 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    
    @staticmethod
    def update_case_status(case_id: str, new_status_code: int, content=None, mode = 'a'):
        
        local_file_locker = os.path.join(config.DIR_MODEL_CASE, case_id, 'lock')
        with open(local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            case_status_directory = os.path.join(config.DIR_MODEL_CASE, case_id, 'status')
            status_code = util.get_filenames(case_status_directory)[0]
        
            if new_status_code == status_code:
                return
            
            old_name = os.path.join(case_status_directory, f'{status_code}')
            new_name = os.path.join(case_status_directory, f'{new_status_code}')
            
            util.rename_file(old_name, new_name, f'CHANGE MCR ({ModelCaseReference.get_model_name(case_id)}: {case_id}) status to {new_status_code}')
            
            if not content == None:
                
                write_content = ''
                write_content += (f'{content}' + '\n')
                
                with open(new_name, mode, encoding='utf-8') as file:
                    file.write(write_content)
            
            portalocker.unlock(lock_file)
    
    @staticmethod
    def get_pre_error_cases(case_id: str):
        
        id_set = { case_id }
        id_stack = util.Stack()
        
        # Initialize error-id stack
        for case_id in get_error_case_ids_in_log(case_id):
            if ModelCaseReference.has_case(case_id):
                id_stack.push(case_id)
        
        # Stack recursion
        while not id_stack.is_empty():
            
            error_id = id_stack.pop()
            id_set.add(error_id)
            
            for case_id in get_error_case_ids_in_log(error_id):
                if ModelCaseReference.has_case(case_id):
                    id_stack.push(case_id)

        return list(id_set)
        
    @staticmethod
    def is_case_error(case_id: str):
        
        case_status_directory = os.path.join(config.DIR_MODEL_CASE, case_id, 'status')
        current_status = int(util.get_filenames(case_status_directory)[0])
    
        is_error = (current_status & config.STATUS_ERROR) == config.STATUS_ERROR
        
        return is_error
    
    
    @staticmethod
    def is_case_done(case_id: str):

        local_file_locker = os.path.join(config.DIR_MODEL_CASE, case_id, 'lock')
        with open(local_file_locker, 'w') as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            
            current_status = int(util.get_filenames(os.path.join(config.DIR_MODEL_CASE, case_id, 'status'))[0])
            is_completed = (current_status & config.STATUS_COMPLETE) == config.STATUS_COMPLETE
            is_error = (current_status & config.STATUS_ERROR) == config.STATUS_ERROR
            
            portalocker.unlock(lock_file)
        
        return is_completed or is_error

