import os
import config
from model import launcher
from app import create_app
from util import StorageMonitor

def initialize_work_space():

    if not os.path.exists(config.DIR_MODEL_CASE):
        os.makedirs(config.DIR_MODEL_CASE)

    if not os.path.exists(config.DIR_GLOBALE_FILE_LOCKER):
        with open (config.DIR_GLOBALE_FILE_LOCKER, 'w') as file:
            pass
        
    for key in config.MODEL_REGISTRY:
        launcher.preheat(key)
         
    StorageMonitor().initialize([config.DIR_ROOT], config.DIR_STORAGE_LOG)

if __name__ == '__main__':
    
    initialize_work_space()

    app = create_app()
    
    app.run(host = "0.0.0.0", port = config.APP_PORT, debug = config.APP_DEBUG)