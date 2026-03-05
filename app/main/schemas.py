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


class CorrectionRules(BaseModel):
    protection_level: Optional[str] = None
    control_level: Optional[str] = None
    hs: Optional[float] = None
    hc: Optional[float] = None
    water_qs: Optional[str] = None
    tidal_level: Optional[str] = None
    other_params: Optional[Dict[str, Any]] = None


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


class BankSegmentCreate(BaseModel):
    segment_id: str
    segment_name: str
    region_code: str
    geometry: GeoJSONGeometry
    dem_id: Optional[str] = None
    bench_id: Optional[str] = None
    ref_id: Optional[str] = None
    hydro_segment: Optional[str] = None
    hydro_year: Optional[str] = None
    hydro_set: Optional[str] = None
    protection_level: Optional[str] = None
    control_level: Optional[str] = None
    other_params: Optional[Dict[str, Any]] = None


class BankSegmentResponse(BankSegmentCreate):
    id: int
    created_at: str
    updated_at: str


class BankSegmentsCreateRequest(BaseModel):
    case_id: str
    segments: List[BankSegmentCreate]
    overwrite: bool = False


class BankSegmentsCreateResponse(BaseModel):
    success: bool
    case_id: str
    inserted_count: int
    segments: List[Dict[str, Any]]


class CrossSectionCreate(BaseModel):
    section_id: str
    section_name: str
    segment_id: str
    region_code: str
    segment_index: Optional[int] = None
    geometry: GeoJSONGeometry
    hs: Optional[float] = None
    hc: Optional[float] = None
    protection_level: Optional[str] = None
    control_level: Optional[str] = None
    water_qs: Optional[str] = None
    tidal_level: Optional[str] = None
    current_timepoint: Optional[str] = None
    comparison_timepoint: Optional[str] = None
    risk_thresholds: Optional[RiskThresholds] = None
    weights: Optional[Weights] = None
    other_params: Optional[Dict[str, Any]] = None


class CrossSectionResponse(CrossSectionCreate):
    id: int
    created_at: str
    updated_at: str


class CrossSectionsCreateRequest(BaseModel):
    case_id: str
    sections: List[CrossSectionCreate]
    inherit_from_segment: bool = True
    overwrite: bool = False


class CrossSectionsCreateResponse(BaseModel):
    success: bool
    case_id: str
    inserted_count: int
    sections: List[Dict[str, Any]]


class CorrectionLineCreate(BaseModel):
    correction_id: str
    geometry: GeoJSONGeometry
    correction_rules: CorrectionRules
    description: Optional[str] = None


class CorrectionLineResponse(CorrectionLineCreate):
    id: int
    created_at: str
    updated_at: str


class CorrectionLinesCreateRequest(BaseModel):
    case_id: str
    corrections: List[CorrectionLineCreate]
    overwrite: bool = False


class CorrectionLinesCreateResponse(BaseModel):
    success: bool
    case_id: str
    inserted_count: int
    corrections: List[Dict[str, Any]]


class FullCaseDataResponse(BaseModel):
    success: bool
    case_id: str
    data: Dict[str, Any]


class ApplyCorrectionsResponse(BaseModel):
    success: bool
    case_id: str
    updated_sections: int
    applied_corrections: int


class EffectiveSectionParamsResponse(BaseModel):
    success: bool
    section_id: str
    effective_params: Dict[str, Any]
    applied_corrections: List[Dict[str, Any]]


class BatchImportRequest(BaseModel):
    case_id: str
    segments: Optional[List[BankSegmentCreate]] = None
    sections: Optional[List[CrossSectionCreate]] = None
    corrections: Optional[List[CorrectionLineCreate]] = None
    overwrite: bool = False


class BatchImportResponse(BaseModel):
    success: bool
    case_id: str
    imported: Dict[str, int]


class ClearCaseResponse(BaseModel):
    success: bool
    case_id: str
    deleted: Dict[str, int]


class GenericSuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None


class GenericErrorResponse(BaseModel):
    success: bool
    error: str
    details: Optional[Dict[str, Any]] = None
