import os
import re
import json
import util
import model
import config
from util import StorageMonitor
from util import db_ops

######################################## Handler for Model Case ########################################


def handle_model_case_status(data: dict):
    case_id = data.get("case-id")
    if not case_id:
        return 400, "Missing 'case-id' in request"

    if not model.ModelCaseReference.has_case(case_id):
        return 404, f"Model Case ID ({case_id}) Not Found"

    return 200, {"status": model.ModelCaseReference.check_case_status(case_id)}


def handle_model_case_error(data: dict):
    case_id = data.get("case-id")
    if not case_id:
        return 400, "Missing 'case-id' in request"

    if not model.ModelCaseReference.has_case(case_id):
        return 404, f"Model Case ID ({case_id}) Not Found"

    # return 200, model.ModelCaseReference.get_status_log(case_id)
    return 200, model.ModelCaseReference.get_simplified_error_log(case_id)


def handle_pre_error_cases(data: dict):
    case_id = data.get("case-id")
    if not case_id:
        return 400, "Missing 'case-id' in request"

    if not model.ModelCaseReference.has_case(case_id):
        return 404, f"Model Case ID ({case_id}) Not Found"

    return 200, {"case-list": model.ModelCaseReference.get_pre_error_cases(case_id)}


def handle_model_case_result(data: dict):
    case_id = data.get("case-id")
    if not case_id:
        return 400, "Missing 'case-id' in request"

    if not model.ModelCaseReference.has_case(case_id):
        return 404, f"Model Case ID ({case_id}) Not Found"

    return 200, {"result": model.ModelCaseReference.get_case_response(case_id)}


def handle_model_case_delete(data: dict):
    case_id = data.get("case-id")
    if not case_id:
        return 400, "Missing 'case-id' in request"

    if not model.ModelCaseReference.delete_case(case_id):
        return 404, f"Model Case ID ({case_id}) Not Found"

    return 200, "OK"


def handle_model_cases_status(request_json: dict):
    case_ids = request_json["case-ids"]
    status_dict = {}

    for case_id in case_ids:
        if not model.ModelCaseReference.has_case(case_id):
            return 404, f"Model Case ID ({case_id}) Not Found"

        status_dict[case_id] = model.ModelCaseReference.check_case_status(case_id)

    return 200, status_dict


def handle_model_cases_call_status():
    response = {"timestamps": []}

    if not os.path.exists(config.DIR_MODEL_CASE):
        return response

    directories = os.listdir(config.DIR_MODEL_CASE)
    case_ids = [
        f for f in directories if os.path.isdir(os.path.join(config.DIR_MODEL_CASE, f))
    ]

    for case_id in case_ids:
        status = "UNLOCK"
        is_locked = model.ModelCaseReference.is_case_locked(case_id)
        if is_locked is None:
            continue
        elif is_locked:
            status = "LOCK"

        response["timestamps"].append(
            {
                "id": case_id,
                "time": model.ModelCaseReference.get_case_time(case_id),
                "status": status,
            }
        )

    response["timestamps"].sort(key=lambda case: case["time"], reverse=True)

    return response


def handle_model_cases_serialization(request_json: dict):
    case_ids = request_json["case-ids"]

    response = {"serialization-list": []}

    for case_id in case_ids:
        if not os.path.exists(os.path.join(config.DIR_MODEL_CASE, case_id)):
            return 404, f"Model Case ID ({case_id}) Not Found"

        with open(
            os.path.join(config.DIR_MODEL_CASE, case_id, "identity.json"),
            "r",
            encoding="utf-8",
        ) as file:
            serialization_data = json.load(file)
            response["serialization-list"].append(
                {"id": case_id, "serialization": serialization_data}
            )

    return 200, response


def handle_model_cases_delete(request_json: dict):
    case_ids = request_json["case-ids"]

    for case_id in case_ids:
        if not model.ModelCaseReference.delete_case(case_id):
            return 404, f"Model Case ID ({case_id}) Not Found"

        # Skip if model case is runnig
        if model.ModelCaseReference.is_case_locked(case_id):
            continue

    return 200, "OK"


######################################## Handler for File System ########################################


def handle_model_case_file(case_id: str, filename: str):
    file_path = os.path.join(config.DIR_MODEL_CASE, case_id, "result", filename)
    mcr = model.ModelCaseReference.open_case(case_id)

    if not os.path.exists(file_path):
        return 404, "Filename Not Found"
    if mcr == None:
        return 404, f"Model Case ID ({case_id}) Not Found"

    return 200, file_path


def handle_resource_file(directory: str):
    file_path = os.path.join(config.DIR_RESOURCE, directory)

    if not os.path.exists(file_path):
        return 404, "Filename Not Found"

    return 200, file_path


def handle_model_case_zip(case_id: str):
    mcr = model.ModelCaseReference.open_case(case_id)
    if mcr == None:
        return 404, f"Model Case ID ({case_id}) Not Found"

    return 200, mcr.result_packaging()


def handl_file_disk_usage():
    # sizes, total_size = util.get_folders_size_parallel([config.DIR_MODEL_CASE, config.DIR_RESOURCE])
    return {"usage": StorageMonitor().get_size()}


def handle_resource_hydrodynamic_list():
    resposne = {"resource": []}

    segment_names = util.get_directories(config.DIR_RESOURCE_HYDRODYNAMIC)
    for segment_name in segment_names:
        segment = {"name": segment_name, "date": []}

        year_names = util.get_directories(
            os.path.join(config.DIR_RESOURCE_HYDRODYNAMIC, segment_name)
        )
        for year_name in year_names:
            year = {"year": year_name, "sets": []}

            set_names = util.get_directories(
                os.path.join(config.DIR_RESOURCE_HYDRODYNAMIC, segment_name, year_name)
            )
            for set_name in set_names:
                set = {"name": set_name, "list": []}

                case_names = util.get_directories(
                    os.path.join(
                        config.DIR_RESOURCE_HYDRODYNAMIC,
                        segment_name,
                        year_name,
                        set_name,
                    ),
                    ["shp", "geojson"],
                )
                for case_name in case_names:
                    with open(
                        os.path.join(
                            config.DIR_RESOURCE_HYDRODYNAMIC,
                            segment_name,
                            year_name,
                            set_name,
                            case_name,
                            "description.json",
                        )
                    ) as file:
                        desc = json.load(file)

                    case = {"name": case_name, "temp": desc["temp"]}
                    set["list"].append(case)
                year["sets"].append(set)
            segment["date"].append(year)
        resposne["resource"].append(segment)

    return resposne


def hadle_resource_hydrodynamic_upload(
    segment: str, year: str, set: str, name: str, temp: bool, boundary: str
):
    model.launch_hydrodynamic_resource_generate(
        segment, year, set, name, str(temp), boundary
    )

    return 200


def handle_resource_directory_delete(directory: str):
    resource_dir = os.path.join(config.DIR_RESOURCE, os.path.normpath(directory))
    if not os.path.exists(resource_dir):
        return 404, f"Directory {resource_dir} does not exist"

    util.delete_folder_contents(resource_dir)
    return 200, "OK"


######################################## Handler for Model Runner ########################################


def handle_model_runner(api: str, request_json: dict):
    try:
        return 200, model.launcher.fetch_model_from_API(api).run(
            request_json
        ).make_response()
    except KeyError as e:
        return 404, {"error": f"API not found: {str(e)}"}
    except Exception as e:
        return 500, {"error": f"Model execution failed: {str(e)}"}


api_handlers = {
    # Model Case
    config.API_MC_ERROR: handle_model_case_error,
    config.API_MC_STATUS: handle_model_case_status,
    config.API_MC_RESULT: handle_model_case_result,
    config.API_MC_DELETE: handle_model_case_delete,
    config.API_MC_PRE_ERROR_CASES: handle_pre_error_cases,
    config.API_MCS_TIME: handle_model_cases_call_status,
    config.API_MCS_STATUS: handle_model_cases_status,
    config.API_MCS_DELETE: handle_model_cases_delete,
    config.API_MCS_SERIALIZATION: handle_model_cases_serialization,
    # File System
    config.API_FS_DISK_USAGE: handl_file_disk_usage,
    config.API_FS_RESULT_ZIP: handle_model_case_zip,
    config.API_FS_RESULT_FILE: handle_model_case_file,
    config.API_FS_RESOURCE_FILE: handle_resource_file,
    config.API_FS_RESOURCE_DELETE: handle_resource_directory_delete,
    config.API_FS_RESOURCE_HYDRODYNAMIC: hadle_resource_hydrodynamic_upload,
    config.API_FS_RESOURCE_HYDRODYNAMIC_LIST: handle_resource_hydrodynamic_list,
}

######################################## Handler for Bank Workflow (重构版) ########################################


def handle_create_banks(data: dict):
    """
    Create banks
    """
    banks = data.get("banks", [])
    overwrite = data.get("overwrite", False)

    inserted_banks = []

    for bank_data in banks:
        try:
            bank_id_db = db_ops.create_bank(
                bank_id=bank_data.get("bank_id"),
                bank_name=bank_data.get("bank_name"),
                region_code=bank_data.get("region_code"),
                geometry=bank_data.get("geometry"),
                bank_geometry=bank_data.get("bank_geometry"),
                description=bank_data.get("description"),
            )
            inserted_banks.append(
                {
                    "id": bank_id_db,
                    "bank_id": bank_data.get("bank_id"),
                    "bank_name": bank_data.get("bank_name"),
                }
            )
        except Exception as e:
            return 400, {"success": False, "error": str(e)}

    return 200, {
        "success": True,
        "inserted_count": len(inserted_banks),
        "banks": inserted_banks,
    }


def handle_get_banks(region_code: str = None):
    """
    Get all banks
    """
    try:
        banks = db_ops.get_banks(region_code=region_code)
        return 200, {"success": True, "banks": banks}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_get_bank(bank_id: str):
    """
    Get a single bank
    """
    try:
        bank = db_ops.get_bank(bank_id)
        if bank:
            return 200, {"success": True, "bank": bank}
        else:
            return 404, {"success": False, "error": "Bank not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_delete_bank(bank_id: str):
    """
    Delete a bank
    """
    try:
        deleted = db_ops.delete_bank(bank_id)
        if deleted:
            return 200, {"success": True, "bank_id": bank_id, "deleted": True}
        else:
            return 404, {"success": False, "error": "Bank not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_update_bank(bank_id: str, data: dict):
    """
    Update a bank
    """
    try:
        updated = db_ops.update_bank(bank_id, **data)
        if updated:
            return 200, {"success": True, "bank_id": bank_id, "updated": True}
        else:
            return 404, {"success": False, "error": "Bank not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_create_tasks(data: dict):
    """
    Create tasks
    """
    tasks = data.get("tasks", [])
    overwrite = data.get("overwrite", False)

    inserted_tasks = []

    for task_data in tasks:
        try:
            task_id_db = db_ops.create_task(
                task_id=task_data.get("task_id"),
                task_name=task_data.get("task_name"),
                bank_ids=task_data.get("bank_ids"),
                description=task_data.get("description"),
            )
            inserted_tasks.append(
                {
                    "id": task_id_db,
                    "task_id": task_data.get("task_id"),
                    "task_name": task_data.get("task_name"),
                }
            )
        except Exception as e:
            return 400, {"success": False, "error": str(e)}

    return 200, {
        "success": True,
        "inserted_count": len(inserted_tasks),
        "tasks": inserted_tasks,
    }


def handle_get_tasks():
    """
    Get all tasks
    """
    try:
        tasks = db_ops.get_tasks()
        return 200, {"success": True, "tasks": tasks}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_get_task(task_id: str):
    """
    Get a single task
    """
    try:
        task = db_ops.get_task(task_id)
        if task:
            return 200, {"success": True, "task": task}
        else:
            return 404, {"success": False, "error": "Task not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_delete_task(task_id: str):
    """
    Delete a task
    """
    try:
        deleted = db_ops.delete_task(task_id)
        if deleted:
            return 200, {"success": True, "task_id": task_id, "deleted": True}
        else:
            return 404, {"success": False, "error": "Task not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_create_basic_params(data: dict):
    """
    Create basic parameters
    """
    params = data.get("params", [])
    overwrite = data.get("overwrite", False)

    inserted_params = []

    for param_data in params:
        try:
            param_id_db = db_ops.create_basic_param(
                param_id=param_data.get("param_id"),
                param_name=param_data.get("param_name"),
                segment=param_data.get("segment"),
                current_timepoint=param_data.get("current_timepoint"),
                set_name=param_data.get("set_name"),
                water_qs=param_data.get("water_qs"),
                tidal_level=param_data.get("tidal_level"),
                bench_id=param_data.get("bench_id"),
                ref_id=param_data.get("ref_id"),
                hs=param_data.get("hs"),
                hc=param_data.get("hc"),
                protection_level=param_data.get("protection_level"),
                control_level=param_data.get("control_level"),
                comparison_timepoint=param_data.get("comparison_timepoint"),
                risk_thresholds=param_data.get("risk_thresholds"),
                weights=param_data.get("weights"),
                other_params=param_data.get("other_params"),
            )
            inserted_params.append(
                {
                    "id": param_id_db,
                    "param_id": param_data.get("param_id"),
                    "param_name": param_data.get("param_name"),
                }
            )
        except Exception as e:
            return 400, {"success": False, "error": str(e)}

    return 200, {
        "success": True,
        "inserted_count": len(inserted_params),
        "params": inserted_params,
    }


def handle_get_basic_params():
    """
    Get all basic parameters
    """
    try:
        params = db_ops.get_basic_params()
        return 200, {"success": True, "params": params}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_get_basic_param(param_id: str):
    """
    Get a single basic param
    """
    try:
        param = db_ops.get_basic_param(param_id)
        if param:
            return 200, {"success": True, "param": param}
        else:
            return 404, {"success": False, "error": "Basic param not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_update_basic_param(param_id: str, data: dict):
    """
    Update basic parameters
    """
    try:
        updated = db_ops.update_basic_param(param_id, **data)
        if updated:
            return 200, {"success": True, "param_id": param_id, "updated": True}
        else:
            return 404, {"success": False, "error": "Basic param not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_create_sections(data: dict):
    """
    Create cross sections (重构版 - 每个section独立存储参数)
    """
    task_id = data.get("task_id")
    sections = data.get("sections", [])
    inherit_from_basic_param = data.get("inherit_from_basic_param", True)
    overwrite = data.get("overwrite", False)

    task = db_ops.get_task(task_id)
    if not task:
        return 404, {"success": False, "error": "Task not found"}

    task_id_db = task["id"]

    inserted_sections = []

    for section_data in sections:
        try:
            # 准备参数字段
            param_fields = {}

            # 如果提供了basic_param_id，从basic_params表复制参数
            basic_param_id = section_data.get("basic_param_id")
            if basic_param_id and inherit_from_basic_param:
                basic_param = db_ops.get_basic_param_by_id(basic_param_id)
                if basic_param:
                    # 复制所有参数字段
                    param_fields = {
                        "param_name": basic_param.get("param_name"),
                        "segment": basic_param.get("segment"),
                        "current_timepoint": basic_param.get("current_timepoint"),
                        "set_name": basic_param.get("set_name"),
                        "water_qs": basic_param.get("water_qs"),
                        "tidal_level": basic_param.get("tidal_level"),
                        "bench_id": basic_param.get("bench_id"),
                        "ref_id": basic_param.get("ref_id"),
                        "hs": basic_param.get("hs"),
                        "hc": basic_param.get("hc"),
                        "protection_level": basic_param.get("protection_level"),
                        "control_level": basic_param.get("control_level"),
                        "comparison_timepoint": basic_param.get("comparison_timepoint"),
                        "risk_thresholds": basic_param.get("risk_thresholds"),
                        "weights": basic_param.get("weights"),
                        "other_params": basic_param.get("other_params"),
                    }

            # 如果section_data中直接提供了参数字段，使用这些值（覆盖继承的值）
            for field in [
                "param_name",
                "segment",
                "current_timepoint",
                "set_name",
                "water_qs",
                "tidal_level",
                "bench_id",
                "ref_id",
                "hs",
                "hc",
                "protection_level",
                "control_level",
                "comparison_timepoint",
                "risk_thresholds",
                "weights",
                "other_params",
            ]:
                if field in section_data and section_data[field] is not None:
                    param_fields[field] = section_data[field]

            section_id_db = db_ops.create_cross_section(
                task_id_db=task_id_db,
                section_id=section_data.get("section_id"),
                section_name=section_data.get("section_name"),
                bank_id=section_data.get("bank_id"),
                region_code=section_data.get("region_code"),
                segment_index=section_data.get("segment_index"),
                geometry=section_data.get("geometry"),
                section_geometry=section_data.get("section_geometry"),
                distance=section_data.get("distance"),
                basic_param_id=basic_param_id,
                **param_fields,
            )
            inserted_sections.append(
                {
                    "id": section_id_db,
                    "section_id": section_data.get("section_id"),
                    "section_name": section_data.get("section_name"),
                    "bank_id": section_data.get("bank_id"),
                }
            )
        except Exception as e:
            return 400, {"success": False, "error": str(e)}

    return 200, {
        "success": True,
        "task_id": task_id,
        "inserted_count": len(inserted_sections),
        "sections": inserted_sections,
    }


def handle_get_sections(task_id: str = None, bank_id: str = None):
    """
    Get cross sections (重构版)
    """
    try:
        task_id_db = None
        if task_id:
            task = db_ops.get_task(task_id)
            if task:
                task_id_db = task["id"]

        sections = db_ops.get_cross_sections(task_id_db=task_id_db, bank_id=bank_id)
        return 200, {"success": True, "task_id": task_id, "sections": sections}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_get_section(section_id: str):
    """
    Get a single cross section
    """
    try:
        section = db_ops.get_cross_section(section_id)
        if section:
            return 200, {"success": True, "section": section}
        else:
            return 404, {"success": False, "error": "Section not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_delete_section(section_id: str):
    """
    Delete a cross section
    """
    try:
        deleted = db_ops.delete_cross_section(section_id)
        if deleted:
            return 200, {"success": True, "section_id": section_id, "deleted": True}
        else:
            return 404, {"success": False, "error": "Section not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_update_section(section_id: str, data: dict):
    """
    Update a cross section
    """
    try:
        updated = db_ops.update_cross_section(section_id, **data)
        if updated:
            return 200, {"success": True, "section_id": section_id, "updated": True}
        else:
            return 404, {"success": False, "error": "Section not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_get_full_task(task_id: str):
    """
    Get full task data (task + sections)
    """
    try:
        full_data = db_ops.get_full_task_data(task_id)
        if full_data:
            return 200, {"success": True, "task_id": task_id, "data": full_data}
        else:
            return 404, {"success": False, "error": "Task not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_update_task_status(task_id: str, data: dict):
    """
    Update task status
    """
    try:
        updated = db_ops.update_task_status(
            task_id=task_id,
            status=data.get("status"),
            run_started_at=data.get("run_started_at"),
            run_completed_at=data.get("run_completed_at"),
            error_message=data.get("error_message"),
        )
        if updated:
            return 200, {"success": True, "task_id": task_id, "updated": True}
        else:
            return 404, {"success": False, "error": "Task not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_run_task(task_id: str):
    """
    Run a task - execute model for all sections in the task
    """
    import datetime

    try:
        task = db_ops.get_task(task_id)
        if not task:
            return 404, {"success": False, "error": "Task not found"}

        task_id_db = task["id"]

        sections = db_ops.get_cross_sections(task_id_db=task_id_db)
        if not sections:
            return 400, {"success": False, "error": "No sections found for this task"}

        now = datetime.datetime.now().isoformat()

        db_ops.update_task_status(
            task_id=task_id,
            status="running",
            run_started_at=now,
            run_completed_at=None,
            error_message=None,
        )

        results = []
        for section in sections:
            try:
                request_json = {
                    "segment": section.get("segment"),
                    "current-timepoint": section.get("current_timepoint"),
                    "set": section.get("set_name"),
                    "water-qs": section.get("water_qs"),
                    "tidal-level": section.get("tidal_level"),
                    "bench-id": section.get("bench_id"),
                    "ref-id": section.get("ref_id"),
                    "hs": section.get("hs"),
                    "hc": section.get("hc"),
                    "protection-level": section.get("protection_level"),
                    "control-level": section.get("control_level"),
                    "comparison-timepoint": section.get("comparison_timepoint"),
                    "risk-thresholds": section.get("risk_thresholds") or "NONE",
                    "wRE": section.get("weights", {}).get("wRE")
                    if section.get("weights")
                    else "NONE",
                    "wNM": section.get("weights", {}).get("wNM")
                    if section.get("weights")
                    else "NONE",
                    "wGE": section.get("weights", {}).get("wGE")
                    if section.get("weights")
                    else "NONE",
                    "wRL": section.get("weights", {}).get("wRL")
                    if section.get("weights")
                    else "NONE",
                    "section-geometry": section.get("section_geometry"),
                }

                status, response = handle_model_runner(
                    config.API_MI_RISK_LEVEL, request_json
                )

                results.append(
                    {
                        "section_id": section.get("section_id"),
                        "status": status,
                        "response": response,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "section_id": section.get("section_id"),
                        "status": 500,
                        "error": str(e),
                    }
                )

        completed_at = datetime.datetime.now().isoformat()

        has_errors = any(r.get("status") != 200 for r in results)

        db_ops.update_task_status(
            task_id=task_id,
            status="error" if has_errors else "completed",
            run_completed_at=completed_at,
            error_message="Some sections failed" if has_errors else None,
        )

        return 200, {
            "success": True,
            "task_id": task_id,
            "status": "error" if has_errors else "completed",
            "results": results,
        }

    except Exception as e:
        import datetime

        db_ops.update_task_status(
            task_id=task_id,
            status="error",
            error_message=str(e),
        )
        return 500, {"success": False, "error": str(e)}


def handle_get_bank_risk_results(
    task_id: Optional[str] = None,
    bank_id: Optional[str] = None,
    region_code: Optional[str] = None,
):
    """
    Get bank risk results
    """
    try:
        results = db_ops.get_bank_risk_results(
            task_id=task_id,
            bank_id=bank_id,
            region_code=region_code,
        )
        return 200, {"success": True, "results": results}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_get_bank_risk_result(result_id: int):
    """
    Get a single bank risk result
    """
    try:
        result = db_ops.get_bank_risk_result(result_id)
        if result:
            return 200, {"success": True, "result": result}
        else:
            return 404, {"success": False, "error": "Result not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_clear_task(task_id: str):
    """
    Clear all data for a task (but keep the task itself)
    """
    try:
        deleted = db_ops.clear_task_data(task_id)
        if deleted is not None:
            return 200, {"success": True, "task_id": task_id, "deleted": deleted}
        else:
            return 404, {"success": False, "error": "Task not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_execute_task(task_id: str):
    """
    Trigger the execution of a task
    """
    # 动态导入，避免循环引用
    # 由于 tasks.py 在 app/tasks.py 而不是 app/main/tasks.py
    # 我们需要在 app 模块下导入
    from app.tasks import task_runner

    success, message = task_runner.start_task(task_id)
    if success:
        return 200, {"success": True, "message": message, "task_id": task_id}
    else:
        return 400, {"success": False, "error": message}


bank_workflow_handlers = {
    "create_banks": handle_create_banks,
    "get_banks": handle_get_banks,
    "get_bank": handle_get_bank,
    "update_bank": handle_update_bank,
    "delete_bank": handle_delete_bank,
    "create_tasks": handle_create_tasks,
    "get_tasks": handle_get_tasks,
    "get_task": handle_get_task,
    "delete_task": handle_delete_task,
    "update_task_status": handle_update_task_status,
    "run_task": handle_run_task,
    "create_basic_params": handle_create_basic_params,
    "get_basic_params": handle_get_basic_params,
    "get_basic_param": handle_get_basic_param,
    "update_basic_param": handle_update_basic_param,
    "create_sections": handle_create_sections,
    "get_sections": handle_get_sections,
    "get_section": handle_get_section,
    "update_section": handle_update_section,
    "delete_section": handle_delete_section,
    "get_full_task": handle_get_full_task,
    "clear_task": handle_clear_task,
    "get_bank_risk_results": handle_get_bank_risk_results,
    "get_bank_risk_result": handle_get_bank_risk_result,
}
