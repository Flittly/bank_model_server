import os
import sys
import json

module_path = os.path.abspath(os.path.join(os.getcwd()))
if module_path not in sys.path:
    sys.path.append(module_path)

import config
import model

def compute_flow_equivalent(segment, year, risk_threshold):
    
    if risk_threshold == "NONE":
        with open(config.DIR_RESOURCE_RISKLEVEL_THRESHOLD_TEMPLATE, 'r', encoding='utf-8') as file: 
            risk_threshold = json.load(file).get("PQ")
        
    PQ_path = os.path.join(config.DIR_RESOURCE_JSON, segment, year, 'standard', 'PQ', 'pq.json')
    if not os.path.exists(PQ_path):
        PQ_path = config.DIR_RESOURCE_PQ_TEMPLATE
    with open(PQ_path, 'r', encoding='utf-8') as file:
        PQ_dict = json.load(file)
        
    years = sorted(PQ_dict.keys())
    year_min = years[0]
    year_max = years[-1]
    year = max(year_min, min(year_max, year))
    
    PQ = PQ_dict[year]
    
    risk = []
    
    if PQ < risk_threshold[0]:
        risk = [1,0,0,0]
    elif PQ < risk_threshold[1]:
        risk = [0,1,0,0]
    elif PQ < risk_threshold[2]:
        risk = [0,0,1,0]
    elif PQ >= risk_threshold[2]:
        risk = [0,0,0,1]

    return PQ, risk
    
##########################################################################################

@model.model_status_controller_sync
def run_flow_equivalent_mcr(mcr: model.ModelCaseReference):
    
    segment = mcr.request_json['segment']
    year = mcr.request_json['year']
    risk_threshold = mcr.request_json['risk-threshold']

    PQ, risk = compute_flow_equivalent(segment, year, risk_threshold)

    return {
        
        'case-id': mcr.id,
        'PQ': PQ,
        'risk-level': risk
    }
    
##########################################################################################

NAME = 'Flow Equivalent'

CATEGORY = 'Multiple Indicators'

CATEGORY_ALIAS = 'mi'
 
def PARSING(self, request_json: dict, model_path: str, other_dependent_ids: list[str]=[]):

    flow_equivalent_mcr = model.ModelCaseReference.create(config.API_MI_FLOW_EQUIVALENT, request_json, NAME, model_path, other_dependent_ids)
    
    return [flow_equivalent_mcr]

def RESPONSING(self, core_mcr: model.ModelCaseReference, default_pre_mcrs: list[model.ModelCaseReference], other_pre_mcrs: list[model.ModelCaseReference]):
    
    return core_mcr.make_response({
                                    'case-id': 'TEMPLATE',
                                    'PQ': 'NONE',
                                    'risk-level': 'NONE'
                                })
    
##########################################################################################

if __name__ == '__main__':

    v1 = sys.argv[1]    # flow equivalent model case reference id

    mcr = model.ModelCaseReference.open_case(v1)

    # Run model case (Flow Equivalent)
    run_flow_equivalent_mcr(mcr)