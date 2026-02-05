from pydantic import BaseModel
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
    model_input: Dict[str, Any] = None
    files: Dict[str, UploadFile] = None

class ModelRunnerResponse(BaseModel):
    result: Dict[str, Any]
    status_code: int

class ErrorResponse(BaseModel):
    detail: str
    status_code: int

class SuccessResponse(BaseModel):
    message: str
    status_code: int