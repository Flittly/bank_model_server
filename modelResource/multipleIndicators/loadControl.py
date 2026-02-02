import os
import sys

module_path = os.path.abspath(os.path.join(os.getcwd()))
if module_path not in sys.path:
    sys.path.append(module_path)

import model
import config

def compute_load_control(protection_level):
    
    risk = []

    if protection_level == "strict":
        risk = [1,0,0,0]
    elif protection_level == "normal":
        risk = [0,1,0,0]
    elif protection_level == "low":
        risk = [0,0,1,0]
    elif protection_level == "no":
        risk = [0,0,0,1]

    return risk
    
##########################################################################################

@model.model_status_controller_sync
def run_load_control_mcr(mcr: model.ModelCaseReference):
    
    control_level = mcr.request_json['control-level']

    risk = compute_load_control(control_level)

    return {
        
        'case-id': mcr.id,
        'risk-level': risk
    }
    
##########################################################################################

NAME = 'Load Control'

CATEGORY = 'Multiple Indicators'

CATEGORY_ALIAS = 'mi'
 
def PARSING(self, request_json: dict, model_path: str, other_dependent_ids: list[str]=[]):

    load_control_mcr = model.ModelCaseReference.create(config.API_MI_LOAD_CONTROL, request_json, NAME, model_path, other_dependent_ids)
    
    return [load_control_mcr]

def RESPONSING(self, core_mcr: model.ModelCaseReference, default_pre_mcrs: list[model.ModelCaseReference], other_pre_mcrs: list[model.ModelCaseReference]):
    
    return core_mcr.make_response({
                                    'case-id': 'TEMPLATE',
                                    'risk-level': 'NONE'
                                })
    
##########################################################################################

if __name__ == '__main__':

    v1 = sys.argv[1]    # load control model case reference id

    mcr = model.ModelCaseReference.open_case(v1)

    # Run model case (Load Control)
    run_load_control_mcr(mcr)