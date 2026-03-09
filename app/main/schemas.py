from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from fastapi import UploadFile, Form


class CaseId(BaseModel):
    id: str


class CaseIds(BaseModel):
    case_ids: List[str]


class ModelCaseStatus(BaseModel):
    status: str


class ModelCaseResult(BaseModel):
    result: Dict[str, Any]


class ModelCaseError(BaseModel):
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class CaseTimestamp(BaseModel):
    id: str
    time: str
    status: str


class CallTimeResponse(BaseModel):
    timestamps: List[CaseTimestamp]


class SerializationItem(BaseModel):
    id: str
    serialization: Dict[str, Any]


class SerializationResponse(BaseModel):
    serialization_list: List[SerializationItem]


class ResourceUpload(BaseModel):
    segment: str
    year: str
    set: str
    name: str
    temp: bool = False
    boundary: Optional[str] = None


class HydrodynamicListResponse(BaseModel):
    resource: List[Dict[str, Any]]


class DiskUsageResponse(BaseModel):
    usage: Dict[str, Any]


class ModelRunnerRequest(BaseModel):
    model_input: Optional[Dict[str, Any]] = None
    files: Optional[Dict[str, UploadFile]] = None


class ModelRunnerResponse(BaseModel):
    result: Dict[str, Any]
    status_code: int


class ErrorResponse(BaseModel):
    detail: str
    status_code: int


class SuccessResponse(BaseModel):
    message: str
    status_code: int


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: List[Any]


class RiskThresholds(BaseModel):
    Dsed: Optional[List[float]] = None
    Zb: Optional[List[float]] = None
    Sa: Optional[List[float]] = None
    Ln: Optional[List[float]] = None
    PQ: Optional[List[float]] = None
    Ky: Optional[List[float]] = None
    Zd: Optional[List[float]] = None
    all: Optional[List[float]] = None


class Weights(BaseModel):
    wRE: Optional[List[float]] = None
    wNM: Optional[List[float]] = None
    wGE: Optional[List[float]] = None
    wRL: Optional[List[float]] = None


# ========================================
# Bank 相关 Schema
# ========================================


class BankCreate(BaseModel):
    bank_id: str
    bank_name: str
    region_code: str
    geometry: GeoJSONGeometry
    bank_geometry: Optional[GeoJSONGeometry] = None
    description: Optional[str] = None


class BankResponse(BankCreate):
    id: int
    created_at: str
    updated_at: str


class BanksCreateRequest(BaseModel):
    banks: List[BankCreate]
    overwrite: bool = False


class BanksCreateResponse(BaseModel):
    success: bool
    inserted_count: int
    banks: List[Dict[str, Any]]


class BankUpdate(BaseModel):
    bank_name: Optional[str] = None
    region_code: Optional[str] = None
    geometry: Optional[GeoJSONGeometry] = None
    bank_geometry: Optional[GeoJSONGeometry] = None
    description: Optional[str] = None


# ========================================
# Task 相关 Schema
# ========================================


class TaskCreate(BaseModel):
    task_id: str
    task_name: str
    bank_ids: Optional[List[str]] = None
    description: Optional[str] = None


class TaskResponse(TaskCreate):
    id: int
    status: Optional[str] = None
    run_started_at: Optional[str] = None
    run_completed_at: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class TaskStatusUpdate(BaseModel):
    status: str
    run_started_at: Optional[str] = None
    run_completed_at: Optional[str] = None
    error_message: Optional[str] = None


class TasksCreateRequest(BaseModel):
    tasks: List[TaskCreate]
    overwrite: bool = False


class TasksCreateResponse(BaseModel):
    success: bool
    inserted_count: int
    tasks: List[Dict[str, Any]]


# ========================================
# Basic Params 相关 Schema
# ========================================


class BasicParamCreate(BaseModel):
    param_id: str
    param_name: str

    # 基础参数
    segment: Optional[str] = None
    current_timepoint: Optional[str] = None
    set_name: Optional[str] = None
    water_qs: Optional[str] = None
    tidal_level: Optional[str] = None

    # DEM参数
    bench_id: Optional[str] = None
    ref_id: Optional[str] = None

    # 水深参数
    hs: Optional[float] = None
    hc: Optional[float] = None

    # 防护控制参数
    protection_level: Optional[str] = None
    control_level: Optional[str] = None

    # 对比时间点
    comparison_timepoint: Optional[str] = None

    # 风险阈值
    risk_thresholds: Optional[RiskThresholds] = None

    # 权重参数
    weights: Optional[Weights] = None

    # 其他参数
    other_params: Optional[Dict[str, Any]] = None


class BasicParamResponse(BasicParamCreate):
    id: int
    created_at: str
    updated_at: str


class BasicParamsCreateRequest(BaseModel):
    params: List[BasicParamCreate]
    overwrite: bool = False


class BasicParamsCreateResponse(BaseModel):
    success: bool
    inserted_count: int
    params: List[Dict[str, Any]]


class BasicParamUpdate(BaseModel):
    param_name: Optional[str] = None
    segment: Optional[str] = None
    current_timepoint: Optional[str] = None
    set_name: Optional[str] = None
    water_qs: Optional[str] = None
    tidal_level: Optional[str] = None
    bench_id: Optional[str] = None
    ref_id: Optional[str] = None
    hs: Optional[float] = None
    hc: Optional[float] = None
    protection_level: Optional[str] = None
    control_level: Optional[str] = None
    comparison_timepoint: Optional[str] = None
    risk_thresholds: Optional[RiskThresholds] = None
    weights: Optional[Weights] = None
    other_params: Optional[Dict[str, Any]] = None


# ========================================
# Cross Section 相关 Schema（重构版）
# ========================================


class CrossSectionCreate(BaseModel):
    section_id: str
    section_name: str
    bank_id: str
    region_code: str
    segment_index: Optional[int] = None
    geometry: GeoJSONGeometry
    section_geometry: Optional[GeoJSONGeometry] = None
    distance: Optional[float] = None
    basic_param_id: Optional[int] = None

    # Section独立的参数字段
    param_name: Optional[str] = None
    segment: Optional[str] = None
    current_timepoint: Optional[str] = None
    set_name: Optional[str] = None
    water_qs: Optional[str] = None
    tidal_level: Optional[str] = None
    bench_id: Optional[str] = None
    ref_id: Optional[str] = None
    hs: Optional[float] = None
    hc: Optional[float] = None
    protection_level: Optional[str] = None
    control_level: Optional[str] = None
    comparison_timepoint: Optional[str] = None
    risk_thresholds: Optional[RiskThresholds] = None
    weights: Optional[Weights] = None
    other_params: Optional[Dict[str, Any]] = None


class CrossSectionResponse(CrossSectionCreate):
    id: int
    task_id: Optional[str] = None
    task_name: Optional[str] = None
    created_at: str
    updated_at: str


class CrossSectionsCreateRequest(BaseModel):
    task_id: str
    sections: List[CrossSectionCreate]
    inherit_from_basic_param: bool = True
    overwrite: bool = False


class CrossSectionsCreateResponse(BaseModel):
    success: bool
    task_id: str
    inserted_count: int
    sections: List[Dict[str, Any]]


class CrossSectionUpdate(BaseModel):
    section_name: Optional[str] = None
    bank_id: Optional[str] = None
    region_code: Optional[str] = None
    segment_index: Optional[int] = None
    geometry: Optional[GeoJSONGeometry] = None
    section_geometry: Optional[GeoJSONGeometry] = None
    distance: Optional[float] = None
    basic_param_id: Optional[int] = None

    # Section独立的参数字段
    param_name: Optional[str] = None
    segment: Optional[str] = None
    current_timepoint: Optional[str] = None
    set_name: Optional[str] = None
    water_qs: Optional[str] = None
    tidal_level: Optional[str] = None
    bench_id: Optional[str] = None
    ref_id: Optional[str] = None
    hs: Optional[float] = None
    hc: Optional[float] = None
    protection_level: Optional[str] = None
    control_level: Optional[str] = None
    comparison_timepoint: Optional[str] = None
    risk_thresholds: Optional[RiskThresholds] = None
    weights: Optional[Weights] = None
    other_params: Optional[Dict[str, Any]] = None


# ========================================
# 综合查询相关 Schema
# ========================================


class FullTaskDataResponse(BaseModel):
    success: bool
    task_id: str
    data: Dict[str, Any]


class ClearTaskResponse(BaseModel):
    success: bool
    task_id: str
    deleted: Dict[str, int]


class GenericSuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None


class GenericErrorResponse(BaseModel):
    success: bool
    error: str
    details: Optional[Dict[str, Any]] = None


# ========================================
# 风险结果相关 Schema
# ========================================


class BankRiskResultResponse(BaseModel):
    id: int
    task_id: int
    section_id: int
    section_name: Optional[str] = None
    region_code: Optional[str] = None
    bank_id: Optional[str] = None
    run_time: str
    risk_level: Optional[int] = None
    indicators: Optional[Dict[str, Any]] = None
    geometry: Optional[GeoJSONGeometry] = None


class BankRiskResultsResponse(BaseModel):
    success: bool
    results: List[BankRiskResultResponse]
