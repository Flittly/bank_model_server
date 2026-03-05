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
    return 200, model.launcher.fetch_model_from_API(api).run(
        request_json
    ).make_response()


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

######################################## Handler for Bank Workflow ########################################


def handle_create_segments(data: dict):
    """
    Create bank segments
    """
    case_id = data.get("case_id")
    segments = data.get("segments", [])
    overwrite = data.get("overwrite", False)

    inserted_segments = []

    for segment_data in segments:
        try:
            segment_id_db = db_ops.create_bank_segment(
                case_id=case_id,
                segment_id=segment_data.get("segment_id"),
                segment_name=segment_data.get("segment_name"),
                region_code=segment_data.get("region_code"),
                geometry=segment_data.get("geometry"),
                dem_id=segment_data.get("dem_id"),
                bench_id=segment_data.get("bench_id"),
                ref_id=segment_data.get("ref_id"),
                hydro_segment=segment_data.get("hydro_segment"),
                hydro_year=segment_data.get("hydro_year"),
                hydro_set=segment_data.get("hydro_set"),
                protection_level=segment_data.get("protection_level"),
                control_level=segment_data.get("control_level"),
                other_params=segment_data.get("other_params"),
            )
            inserted_segments.append(
                {
                    "id": segment_id_db,
                    "segment_id": segment_data.get("segment_id"),
                    "segment_name": segment_data.get("segment_name"),
                }
            )
        except Exception as e:
            return 400, {"success": False, "error": str(e)}

    return 200, {
        "success": True,
        "case_id": case_id,
        "inserted_count": len(inserted_segments),
        "segments": inserted_segments,
    }


def handle_get_segments(case_id: str):
    """
    Get bank segments for a case
    """
    try:
        segments = db_ops.get_bank_segments(case_id)
        return 200, {"success": True, "case_id": case_id, "segments": segments}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_delete_segment(case_id: str, segment_id: str):
    """
    Delete a bank segment
    """
    try:
        deleted = db_ops.delete_bank_segment(case_id, segment_id)
        if deleted:
            return 200, {"success": True, "segment_id": segment_id, "deleted": True}
        else:
            return 404, {"success": False, "error": "Segment not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_create_sections(data: dict):
    """
    Create cross sections
    """
    case_id = data.get("case_id")
    sections = data.get("sections", [])
    inherit_from_segment = data.get("inherit_from_segment", True)
    overwrite = data.get("overwrite", False)

    inserted_sections = []

    for section_data in sections:
        try:
            section_id_db = db_ops.create_cross_section(
                case_id=case_id,
                section_id=section_data.get("section_id"),
                section_name=section_data.get("section_name"),
                segment_id_db=section_data.get("segment_id"),
                region_code=section_data.get("region_code"),
                segment_index=section_data.get("segment_index"),
                geometry=section_data.get("geometry"),
                hs=section_data.get("hs"),
                hc=section_data.get("hc"),
                protection_level=section_data.get("protection_level"),
                control_level=section_data.get("control_level"),
                water_qs=section_data.get("water_qs"),
                tidal_level=section_data.get("tidal_level"),
                current_timepoint=section_data.get("current_timepoint"),
                comparison_timepoint=section_data.get("comparison_timepoint"),
                risk_thresholds=section_data.get("risk_thresholds"),
                weights=section_data.get("weights"),
                other_params=section_data.get("other_params"),
            )
            inserted_sections.append(
                {
                    "id": section_id_db,
                    "section_id": section_data.get("section_id"),
                    "section_name": section_data.get("section_name"),
                    "segment_id": section_data.get("segment_id"),
                }
            )
        except Exception as e:
            return 400, {"success": False, "error": str(e)}

    return 200, {
        "success": True,
        "case_id": case_id,
        "inserted_count": len(inserted_sections),
        "sections": inserted_sections,
    }


def handle_get_sections(case_id: str, segment_id: int = None):
    """
    Get cross sections for a case
    """
    try:
        sections = db_ops.get_cross_sections(case_id, segment_id)
        return 200, {"success": True, "case_id": case_id, "sections": sections}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_delete_section(case_id: str, section_id: str):
    """
    Delete a cross section
    """
    try:
        deleted = db_ops.delete_cross_section(case_id, section_id)
        if deleted:
            return 200, {"success": True, "section_id": section_id, "deleted": True}
        else:
            return 404, {"success": False, "error": "Section not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_create_corrections(data: dict):
    """
    Create correction lines
    """
    case_id = data.get("case_id")
    corrections = data.get("corrections", [])
    overwrite = data.get("overwrite", False)

    inserted_corrections = []

    for correction_data in corrections:
        try:
            correction_id_db = db_ops.create_correction_line(
                case_id=case_id,
                correction_id=correction_data.get("correction_id"),
                geometry=correction_data.get("geometry"),
                correction_rules=correction_data.get("correction_rules"),
                description=correction_data.get("description"),
            )
            inserted_corrections.append(
                {
                    "id": correction_id_db,
                    "correction_id": correction_data.get("correction_id"),
                    "description": correction_data.get("description"),
                }
            )
        except Exception as e:
            return 400, {"success": False, "error": str(e)}

    return 200, {
        "success": True,
        "case_id": case_id,
        "inserted_count": len(inserted_corrections),
        "corrections": inserted_corrections,
    }


def handle_get_corrections(case_id: str):
    """
    Get correction lines for a case
    """
    try:
        corrections = db_ops.get_correction_lines(case_id)
        return 200, {"success": True, "case_id": case_id, "corrections": corrections}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_delete_correction(case_id: str, correction_id: str):
    """
    Delete a correction line
    """
    try:
        deleted = db_ops.delete_correction_line(case_id, correction_id)
        if deleted:
            return 200, {
                "success": True,
                "correction_id": correction_id,
                "deleted": True,
            }
        else:
            return 404, {"success": False, "error": "Correction not found"}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_get_full_case(case_id: str):
    """
    Get full case data (segments + sections + corrections)
    """
    try:
        full_data = db_ops.get_full_case_data(case_id)
        return 200, {"success": True, "case_id": case_id, "data": full_data}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


def handle_clear_case(case_id: str):
    """
    Clear all data for a case
    """
    try:
        deleted = db_ops.clear_case_data(case_id)
        return 200, {"success": True, "case_id": case_id, "deleted": deleted}
    except Exception as e:
        return 400, {"success": False, "error": str(e)}


bank_workflow_handlers = {
    "create_segments": handle_create_segments,
    "get_segments": handle_get_segments,
    "delete_segment": handle_delete_segment,
    "create_sections": handle_create_sections,
    "get_sections": handle_get_sections,
    "delete_section": handle_delete_section,
    "create_corrections": handle_create_corrections,
    "get_corrections": handle_get_corrections,
    "delete_correction": handle_delete_correction,
    "get_full_case": handle_get_full_case,
    "clear_case": handle_clear_case,
}
