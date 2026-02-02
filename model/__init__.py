import os
import config
import subprocess
from .modelCaseReference import ModelCaseReference
from .hydrodynamic_resource import generate_hydrodynamic_resource
from .modelLauncher import model_status_controller_sync, ModelLauncher as launcher

def launch_hydrodynamic_resource_generate(segment: str, year: str, set: str, name: str, temp: bool, boundary: str):
    
    # Execute
    command = [
        'python',
        
        os.path.join(config.DIR_MODEL, 'numericalModel/hydrodynamic_resource.py'),
        segment,
        year,
        set,
        name,
        temp,
        boundary
    ]
    
    subprocess.Popen(command)