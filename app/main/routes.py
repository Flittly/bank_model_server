import os
import json
import zipfile
import uuid
import tempfile
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.responses import FileResponse
import util
import config
import model
from . import controllers
from .schemas import (
    CaseId,
    CaseIds,
    ModelCaseStatus,
    ModelCaseResult,
    ModelCaseError,
    CallTimeResponse,
    SerializationResponse,
    DiskUsageResponse,
    ErrorResponse,
    SuccessResponse,
    BanksCreateRequest,
    BanksCreateResponse,
    BankUpdate,
    TasksCreateRequest,
    TasksCreateResponse,
    TaskStatusUpdate,
    BasicParamsCreateRequest,
    BasicParamsCreateResponse,
    BasicParamUpdate,
    CrossSectionsCreateRequest,
    CrossSectionsCreateResponse,
    CrossSectionUpdate,
    FullTaskDataResponse,
    ClearTaskResponse,
    BankRiskResultResponse,
    BankRiskResultsResponse,
    GenericSuccessResponse,
    GenericErrorResponse,
    HydrodynamicListResponse,
)
from . import controllers
from . import (
    api_router,
)


# Helper function
def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.APP_ALLOWED_EXTENSIONS
    )


######################################## API for Model Case ########################################


@api_router.get("/mc/status", response_model=ModelCaseStatus)
async def get_model_case_status(case_id: str):
    status, response = controllers.api_handlers[config.API_MC_STATUS](case_id)
    if status == 200:
        return ModelCaseStatus(status=response)
    raise HTTPException(status_code=404, detail=response)


@api_router.get("/mc/result", response_model=ModelCaseResult)
async def get_model_case_result(case_id: str):
    status, response = controllers.api_handlers[config.API_MC_RESULT](case_id)
    if status == 200:
        return ModelCaseResult(result=response)
    raise HTTPException(status_code=404, detail=response)


@api_router.get("/mc/error", response_model=ModelCaseError)
async def get_model_case_error(case_id: str):
    status, response = controllers.api_handlers[config.API_MC_ERROR](case_id)
    if status == 200:
        return ModelCaseError(**response)
    raise HTTPException(status_code=404, detail=response)


@api_router.get("/mc/pre-error-cases")
async def get_pre_error_cases(case_id: str):
    status, response = controllers.api_handlers[config.API_MC_PRE_ERROR_CASES](case_id)
    if status == 200:
        return response
    raise HTTPException(status_code=404, detail=response)


@api_router.delete("/mc")
async def delete_model_case(case_id: str):
    status, response = controllers.api_handlers[config.API_MC_DELETE](case_id)
    if status == 200:
        return SuccessResponse(message=response, status_code=200)
    raise HTTPException(status_code=404, detail=response)


@api_router.post("/mcs/status", response_model=Dict[str, str])
async def get_model_cases_status(case_ids: CaseIds):
    status, response = controllers.api_handlers[config.API_MCS_STATUS](case_ids.dict())
    if status == 200:
        return response
    raise HTTPException(status_code=404, detail=response)


@api_router.get("/mcs/time", response_model=CallTimeResponse)
async def get_model_cases_call_time():
    response = controllers.api_handlers[config.API_MCS_TIME]()
    return CallTimeResponse(timestamps=response.get("timestamps", []))


@api_router.post("/mcs/serialization", response_model=SerializationResponse)
async def get_model_cases_serialization(case_ids: CaseIds):
    status, response = controllers.api_handlers[config.API_MCS_SERIALIZATION](
        case_ids.dict()
    )
    if status == 200:
        return SerializationResponse(**response)
    raise HTTPException(status_code=404, detail=response)


@api_router.post("/mcs")
async def delete_model_cases(case_ids: CaseIds):
    status, response = controllers.api_handlers[config.API_MCS_DELETE](case_ids.dict())
    if status == 200:
        return SuccessResponse(message=response, status_code=200)
    raise HTTPException(status_code=404, detail=response)


@api_router.delete("/fs/resource")
async def delete_resource_directory(directory: str):
    status, response = controllers.api_handlers[config.API_FS_RESOURCE_DELETE](
        directory
    )
    if status == 200:
        return SuccessResponse(message=response, status_code=200)
    raise HTTPException(status_code=404, detail=response)


######################################## API for File System ########################################


@api_router.get("/fs/result/file")
async def get_model_case_file(case_id: str, filename: str):
    status, file_path = controllers.api_handlers[config.API_FS_RESULT_FILE](
        case_id, filename
    )
    if status == 200:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(
            file_path, media_type="application/octet-stream", filename=filename
        )
    raise HTTPException(status_code=404, detail=file_path)


@api_router.get("/fs/resource/file")
async def get_resource_file(name: str):
    status, file_path = controllers.api_handlers[config.API_FS_RESOURCE_FILE](name)
    if status == 200:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=os.path.basename(file_path),
        )
    raise HTTPException(status_code=404, detail=file_path)


@api_router.get("/fs/result/zip")
async def get_model_case_zip(case_id: str):
    status, zip_path = controllers.api_handlers[config.API_FS_RESULT_ZIP](case_id)
    if status == 200:
        if not os.path.exists(zip_path):
            raise HTTPException(status_code=404, detail="Zip file not found")
        return FileResponse(
            zip_path, media_type="application/zip", filename=os.path.basename(zip_path)
        )
    raise HTTPException(status_code=404, detail=zip_path)


@api_router.post("/fs/resource/zip")
async def upload_resource_zip(file: UploadFile = File(...), json_data: str = Form(...)):
    try:
        request_json = json.loads(json_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    resource_path = os.path.join(config.DIR_RESOURCE, request_json.get("type", ""))
    if not resource_path:
        raise HTTPException(status_code=400, detail="No type specified")

    if not os.path.exists(resource_path):
        os.makedirs(resource_path, exist_ok=True)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    if file and allowed_file(file.filename):
        filename = file.filename
        zip_path = os.path.join(resource_path, filename)

        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(resource_path)

        os.remove(zip_path)
        util.update_size(
            config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(resource_path)
        )

        return SuccessResponse(message="OK", status_code=200)
    else:
        raise HTTPException(status_code=400, detail="File type not allowed")


@api_router.post("/fs/resource/tiff")
async def upload_tiff(file: UploadFile = File(...), json_data: str = Form(...)):
    try:
        request_json = json.loads(json_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    segment = request_json["segment"]
    year = request_json["year"]
    set = request_json["set"]
    name = request_json["name"]
    set_path = os.path.join(config.DIR_RESOURCE_TIFF, segment, year, set)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)

    if file and allowed_file(file.filename):
        filename = file.filename
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)

        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()

        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))

        tiff_extension = None
        if os.path.exists(os.path.join(file_path, name + ".tiff")):
            tiff_extension = "tiff"
        elif os.path.exists(os.path.join(file_path, name + ".tif")):
            tiff_extension = "tif"
        else:
            raise HTTPException(status_code=400, detail="Files Provided Are Incomplete")

        return {
            "directory": f"tiff/{segment}/{year}/{set}/{fn}/{name}.{tiff_extension}"
        }
    else:
        raise HTTPException(status_code=400, detail="File Type Not Allowed")


@api_router.post("/fs/resource/adf")
async def upload_adf(file: UploadFile = File(...), json_data: str = Form(...)):
    try:
        request_json = json.loads(json_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    segment = request_json["segment"]
    year = request_json["year"]
    set = request_json["set"]
    name = request_json["name"]
    set_path = os.path.join(config.DIR_RESOURCE_ADF, segment, year, set)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)

    if file and allowed_file(file.filename):
        filename = file.filename
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)

        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()

        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        adf_path = os.path.join(file_path, name + ".adf")
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))

        if not os.path.exists(adf_path):
            raise HTTPException(status_code=400, detail="Files Provided Are Incomplete")

        return {"directory": f"adf/{segment}/{year}/{set}/{fn}/{name}.adf"}
    else:
        raise HTTPException(status_code=400, detail="File Type Not Allowed")


@api_router.post("/fs/resource/json")
async def upload_json(file: UploadFile = File(...), json_data: str = Form(...)):
    try:
        request_json = json.loads(json_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    segment = request_json["segment"]
    year = request_json["year"]
    set = request_json["set"]
    name = request_json["name"]
    set_path = os.path.join(config.DIR_RESOURCE_JSON, segment, year, set)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)

    if file and allowed_file(file.filename):
        filename = file.filename
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)

        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()

        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        json_path = os.path.join(file_path, name + ".json")
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))

        if not os.path.exists(json_path):
            raise HTTPException(status_code=400, detail="Files Provided Are Incomplete")

        return {"directory": f"json/{segment}/{year}/{set}/{fn}/{name}.json"}
    else:
        raise HTTPException(status_code=400, detail="File Type Not Allowed")


@api_router.post("/fs/resource/geojson")
async def upload_geojson(file: UploadFile = File(...), json_data: str = Form(...)):
    try:
        request_json = json.loads(json_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    segment = request_json["segment"]
    year = request_json["year"]
    set = request_json["set"]
    name = request_json["name"]
    set_path = os.path.join(config.DIR_RESOURCE_GEOJSON, segment, year, set)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)

    if file and allowed_file(file.filename):
        filename = file.filename
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)

        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()

        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        json_path = os.path.join(file_path, name + ".geojson")
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))

        if not os.path.exists(json_path):
            raise HTTPException(status_code=400, detail="Files Provided Are Incomplete")

        return {"directory": f"geojson/{segment}/{year}/{set}/{fn}/{name}.geojson"}
    else:
        raise HTTPException(status_code=400, detail="File Type Not Allowed")


@api_router.post("/fs/resource/shapefile")
async def upload_shapefile(file: UploadFile = File(...), json_data: str = Form(...)):
    try:
        request_json = json.loads(json_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    segment = request_json["segment"]
    year = request_json["year"]
    set = request_json["set"]
    name = request_json["name"]
    set_path = os.path.join(config.DIR_RESOURCE_SHP, segment, year, set)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)

    if file and allowed_file(file.filename):
        filename = file.filename
        zip_path = os.path.join(set_path, filename)
        fn, fe = os.path.splitext(filename)

        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()

        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)
        shp_path = os.path.join(file_path, name + ".shp")
        util.update_size(config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(file_path))

        complete = True
        if not util.contains_extension(file_path, ".shp"):
            complete = False
        if not util.contains_extension(file_path, ".shx"):
            complete = False
        if not util.contains_extension(file_path, ".prj"):
            complete = False
        if not util.contains_extension(file_path, ".dbf"):
            complete = False
        if not os.path.exists(shp_path):
            complete = False
        if not complete:
            raise HTTPException(status_code=400, detail="Files Provided Are Incomplete")

        return {"directory": f"shp/{segment}/{year}/{set}/{fn}/{name}.shp"}
    else:
        raise HTTPException(status_code=400, detail="File Type Not Allowed")


@api_router.post("/fs/resource/hydrodynamic")
async def upload_hydrodynamic_zip(
    file: UploadFile = File(...), json_data: str = Form(...)
):
    try:
        request_json = json.loads(json_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    segment = request_json["segment"]
    year = request_json["year"]
    set = request_json["set"]
    boundary_path = request_json["boundary"]
    set_path = os.path.join(config.DIR_RESOURCE_HYDRODYNAMIC, segment, year, set)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    if not os.path.exists(set_path):
        os.makedirs(set_path, exist_ok=True)

    if file and allowed_file(file.filename):
        filename = file.filename
        fn, fe = os.path.splitext(filename)
        zip_path = os.path.join(set_path, filename)

        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(set_path)
            util.remove_ignore_files_and_directories()

        os.remove(zip_path)
        file_path = os.path.join(set_path, fn)

        complete = True
        if not util.contains_extension(file_path, ".63"):
            complete = False
        if not util.contains_extension(file_path, ".64"):
            complete = False
        if not util.contains_extension(file_path, ".14"):
            complete = False
        if not complete:
            raise HTTPException(status_code=400, detail="Files Provided Are Incomplete")

        status = controllers.api_handlers[config.API_FS_RESOURCE_HYDRODYNAMIC](
            request_json["segment"],
            request_json["year"],
            request_json["set"],
            fn,
            request_json["temp"],
            boundary_path,
        )
        if status == 200:
            return {"directory": f"hydrodynamic/{segment}/{year}/{set}/{fn}/"}
    else:
        raise HTTPException(status_code=400, detail="File Type Not Allowed")


@api_router.get("/fs/usage", response_model=DiskUsageResponse)
async def get_disk_usage():
    response = controllers.api_handlers[config.API_FS_DISK_USAGE]()
    return DiskUsageResponse(**response)


@api_router.get(
    "/fs/resource/hydrodynamic/list", response_model=HydrodynamicListResponse
)
async def get_hydrodynamic_resource_list():
    response = controllers.api_handlers[config.API_FS_RESOURCE_HYDRODYNAMIC_LIST]()
    return HydrodynamicListResponse(**response)


######################################## API for Bank Workflow (重构版) ########################################


@api_router.post("/bank/banks", response_model=BanksCreateResponse)
async def create_banks(request: BanksCreateRequest):
    status, response = controllers.bank_workflow_handlers["create_banks"](
        request.dict()
    )
    if status == 200:
        return BanksCreateResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/banks")
async def get_banks(region_code: Optional[str] = None):
    status, response = controllers.bank_workflow_handlers["get_banks"](region_code)
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/banks/{bank_id}")
async def get_bank(bank_id: str):
    status, response = controllers.bank_workflow_handlers["get_bank"](bank_id)
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.put("/bank/banks/{bank_id}")
async def update_bank(bank_id: str, request: BankUpdate):
    status, response = controllers.bank_workflow_handlers["update_bank"](
        bank_id, request.dict(exclude_none=True)
    )
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.delete("/bank/banks/{bank_id}", response_model=GenericSuccessResponse)
async def delete_bank(bank_id: str):
    status, response = controllers.bank_workflow_handlers["delete_bank"](bank_id)
    if status == 200:
        return GenericSuccessResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.post("/bank/tasks", response_model=TasksCreateResponse)
async def create_tasks(request: TasksCreateRequest):
    status, response = controllers.bank_workflow_handlers["create_tasks"](
        request.dict()
    )
    if status == 200:
        return TasksCreateResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/tasks")
async def get_tasks():
    status, response = controllers.bank_workflow_handlers["get_tasks"]()
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/tasks/{task_id}")
async def get_task(task_id: str):
    status, response = controllers.bank_workflow_handlers["get_task"](task_id)
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.delete("/bank/tasks/{task_id}", response_model=GenericSuccessResponse)
async def delete_task(task_id: str):
    status, response = controllers.bank_workflow_handlers["delete_task"](task_id)
    if status == 200:
        return GenericSuccessResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.put("/bank/tasks/{task_id}/status")
async def update_task_status(task_id: str, request: TaskStatusUpdate):
    status, response = controllers.bank_workflow_handlers["update_task_status"](
        task_id, request.dict(exclude_none=True)
    )
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.post("/bank/tasks/{task_id}/run")
async def run_task(task_id: str):
    status, response = controllers.bank_workflow_handlers["run_task"](task_id)
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.post("/bank/basic-params", response_model=BasicParamsCreateResponse)
async def create_basic_params(request: BasicParamsCreateRequest):
    status, response = controllers.bank_workflow_handlers["create_basic_params"](
        request.dict()
    )
    if status == 200:
        return BasicParamsCreateResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/basic-params")
async def get_basic_params():
    status, response = controllers.bank_workflow_handlers["get_basic_params"]()
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/basic-params/{param_id}")
async def get_basic_param(param_id: str):
    status, response = controllers.bank_workflow_handlers["get_basic_param"](param_id)
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.put("/bank/basic-params/{param_id}")
async def update_basic_param(param_id: str, request: BasicParamUpdate):
    status, response = controllers.bank_workflow_handlers["update_basic_param"](
        param_id, request.dict(exclude_none=True)
    )
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.post("/bank/sections", response_model=CrossSectionsCreateResponse)
async def create_sections(request: CrossSectionsCreateRequest):
    status, response = controllers.bank_workflow_handlers["create_sections"](
        request.dict()
    )
    if status == 200:
        return CrossSectionsCreateResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/sections")
async def get_sections(task_id: Optional[str] = None, bank_id: Optional[str] = None):
    status, response = controllers.bank_workflow_handlers["get_sections"](
        task_id, bank_id
    )
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/sections/{section_id}")
async def get_section(section_id: str):
    status, response = controllers.bank_workflow_handlers["get_section"](section_id)
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.delete("/bank/sections/{section_id}", response_model=GenericSuccessResponse)
async def delete_section(section_id: str):
    status, response = controllers.bank_workflow_handlers["delete_section"](section_id)
    if status == 200:
        return GenericSuccessResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.put("/bank/sections/{section_id}")
async def update_section(section_id: str, request: CrossSectionUpdate):
    status, response = controllers.bank_workflow_handlers["update_section"](
        section_id, request.dict(exclude_none=True)
    )
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/tasks/{task_id}/full", response_model=FullTaskDataResponse)
async def get_full_task(task_id: str):
    status, response = controllers.bank_workflow_handlers["get_full_task"](task_id)
    if status == 200:
        return FullTaskDataResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.delete("/bank/tasks/{task_id}/clear", response_model=ClearTaskResponse)
async def clear_task(task_id: str):
    status, response = controllers.bank_workflow_handlers["clear_task"](task_id)
    if status == 200:
        return ClearTaskResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/results", response_model=BankRiskResultsResponse)
async def get_bank_risk_results(
    task_id: Optional[str] = None,
    bank_id: Optional[str] = None,
    region_code: Optional[str] = None,
):
    status, response = controllers.bank_workflow_handlers["get_bank_risk_results"](
        task_id=task_id,
        bank_id=bank_id,
        region_code=region_code,
    )
    if status == 200:
        return BankRiskResultsResponse(**response)
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.get("/bank/results/{result_id}")
async def get_bank_risk_result(result_id: int):
    status, response = controllers.bank_workflow_handlers["get_bank_risk_result"](
        result_id
    )
    if status == 200:
        return response
    raise HTTPException(
        status_code=status, detail=response.get("error", "Unknown error")
    )


@api_router.post("/tasks/{task_id}/execute")
async def execute_task(task_id: str):
    """
    Execute a task (run risk analysis for all sections)
    """
    status, response = controllers.handle_execute_task(task_id)
    if status == 200:
        return SuccessResponse(message=response.get("message"), status_code=200)
    raise HTTPException(status_code=400, detail=response.get("error"))


######################################## API for Models ########################################


@api_router.get("/{category}/{model_name}")
async def get_model_runner(category: str, model_name: str, request: Request):
    api_path = f"{config.API_VERSION}/{category}/{model_name}"

    if api_path in controllers.api_handlers:
        request_json = dict(request.query_params)
        status, response = controllers.api_handlers[api_path](request_json)
        if status == 200:
            return response
        raise HTTPException(status_code=status, detail=str(response))

    query_params = dict(request.query_params)
    status, response = controllers.handle_model_runner(api_path, query_params)
    if status == 200:
        return response
    raise HTTPException(status_code=status, detail=str(response))


@api_router.post("/{category}/{model_name}")
async def post_model_runner(category: str, model_name: str, request: Request):
    api_path = f"{config.API_VERSION}/{category}/{model_name}"

    form_data = await request.form()
    try:
        json_data = await request.json()
    except:
        json_data = None

    request_json = {}
    if json_data:
        request_json.update(json_data)

    files = {}
    if form_data:
        for key, value in form_data.items():
            if isinstance(value, UploadFile):
                files[key] = value
            else:
                request_json[key] = value

    if api_path in controllers.api_handlers:
        status, response = controllers.api_handlers[api_path](request_json)
        if status == 200:
            return response
        raise HTTPException(status_code=status, detail=str(response))

    if files:
        request_json.update(
            {f"file_{key}": file.filename for key, file in files.items()}
        )

    status, response = controllers.handle_model_runner(api_path, request_json)
    if status == 200:
        return response
    raise HTTPException(status_code=status, detail=str(response))
