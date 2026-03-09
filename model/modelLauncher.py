import os
import sys
import time
import copy
import util
import model
import types
import config
import marshal
import traceback
import threading
import functools
import py_compile
import subprocess
import multiprocessing
from .modelProcess import Process_Queue
from .modelCaseReference import ModelCaseReference as MCR

######################################## AOP ########################################


def model_status_controller_sync(func):
    @functools.wraps(func)
    def wrapper(mcr: MCR, *args, **kwargs):
        # Return if mcr is unlocked (COMPLETE or ERROR)
        if mcr.find_status(config.STATUS_COMPLETE) or mcr.find_status(
            config.STATUS_ERROR
        ):
            return

        # Run
        try:
            mcr.update_status(config.STATUS_LOCK | config.STATUS_RUNNING)
            result = func(mcr, *args, **kwargs)
            mcr.make_response(result)
            mcr.update_status(config.STATUS_UNLOCK | config.STATUS_COMPLETE)
            util.update_size(
                config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(mcr.directory)
            )
            return

        except Exception as e:
            mcr.update_status(config.STATUS_UNLOCK | config.STATUS_ERROR, e, "w")
            util.update_size(
                config.DIR_STORAGE_LOG, util.get_folder_size_in_gb(mcr.directory)
            )
            traceback.print_exc()
            return

    return wrapper


######################################## Utils ########################################


def get_pyc_filename(script_name: str):
    python_version = f"{sys.version_info.major}{sys.version_info.minor}"

    pyc_filename = f"{script_name}.cpython-{python_version}.pyc"
    return pyc_filename


def compile_model_script_to_pyc(model_api: str, script_path: str):
    code_md5 = util.generate_md5(model_api)
    pyc_filename = get_pyc_filename(code_md5)
    compiled_path = os.path.join(config.DIR_RESOURCE_MODEL, code_md5)
    pyc_file_path = os.path.join(compiled_path, pyc_filename)

    script_modified_time = os.path.getmtime(script_path)

    if os.path.exists(compiled_path):
        try:
            with open(
                os.path.join(compiled_path, "time.txt"), "r", encoding="utf-8"
            ) as file:
                program_modified_time = float(file.readline())

            existing_pyc_files = [
                f for f in os.listdir(compiled_path) if f.endswith(".pyc")
            ]
            if existing_pyc_files:
                existing_version = (
                    existing_pyc_files[0].split(".")[-2].replace("cpython-", "")
                )
                current_version = f"{sys.version_info.major}{sys.version_info.minor}"

                if (
                    existing_version != current_version
                    or program_modified_time != script_modified_time
                ):
                    for old_pyc in existing_pyc_files:
                        os.remove(os.path.join(compiled_path, old_pyc))
                else:
                    return
        except FileNotFoundError:
            pass

    if not os.path.exists(compiled_path):
        os.makedirs(compiled_path)

    with open(os.path.join(compiled_path, "time.txt"), "w", encoding="utf-8") as file:
        file.write(str(script_modified_time))

    py_compile.compile(script_path, cfile=pyc_file_path)
    print(
        f"Model Program ({os.path.basename(script_path)}) Is Compiled to .pyc",
        flush=True,
    )


def compile_model_script(model_name: str, script_path: str):
    code_md5 = util.generate_md5(model_name)
    compiled_path = os.path.join(config.DIR_RESOURCE_MODEL, code_md5)

    if os.path.exists(compiled_path):
        try:
            with open(
                os.path.join(compiled_path, "time.txt"), "r", encoding="utf-8"
            ) as file:
                program_modified_time = float(file.readline())
                script_modified_time = os.path.getmtime(script_path)
                if program_modified_time == script_modified_time:
                    return
        except FileNotFoundError:
            pass

    with open(script_path, "r", encoding="utf-8") as file:
        script = file.read()
    compiled_code = compile(script, model_name, "exec")

    if not os.path.exists(compiled_path):
        os.makedirs(compiled_path)

    with open(os.path.join(compiled_path, "program.marshal"), "wb") as file:
        marshal.dump(compiled_code, file)

    with open(os.path.join(compiled_path, "time.txt"), "w", encoding="utf-8") as file:
        file.write(str(os.path.getmtime(script_path)))

    print(f"Model Program ({model_name}) Is Compiled", flush=True)


def load_code_from_pyc(pyc_path: str):
    with open(pyc_path, "rb") as f:
        f.read(16)  # Skip the .pyc header (timestamp, magic number, etc.)
        code_obj = marshal.load(f)
    return code_obj


def monitor_subprocess(args: list[str]):
    ids = copy.deepcopy(args)
    args.insert(0, sys.executable)

    try:
        process = subprocess.Popen(args)

        while True:
            return_code = process.poll()

            if return_code is None:
                pass
            else:
                break
            time.sleep(3)

    except OSError as e:
        print(f"Error Happened When Model Case Is Running: {e}", flush=True)

    finally:
        if process.poll() is None:
            process.kill()
            for id in ids:
                mcr = MCR.open_case(id)
                if mcr.find_status(config.STATUS_LOCK):
                    mcr.update_status(
                        config.STATUS_ERROR | config.STATUS_UNLOCK,
                        "Unexpected Error Happend!",
                    )


def safe_launcher(command: list[str]):
    threading.Thread(target=monitor_subprocess, args=(command,)).start()


######################################## Model Launcher ########################################

# TODO: Need to check whether mcrs is valid
# @model_status_controller_async
# def mcr_checker(mcrs: list[MCR]):
#     pass


def mcr_checker(mcrs: list[MCR]):
    core_mcr = mcrs[-1]
    other_mcrs = mcrs[:-1]

    # Returen if core model case is being used or used
    if core_mcr.is_used():
        return False

    # Return if any other model cases is error
    error_case_ids = []
    for mcr in other_mcrs:
        if mcr.find_status(config.STATUS_ERROR):
            error_case_ids.append(mcr.id)
    if len(error_case_ids):
        error_log = MCR.generate_pre_error_log(core_mcr.id, error_case_ids)
        core_mcr.update_status(
            config.STATUS_ERROR | config.STATUS_UNLOCK, error_log, "w"
        )
        return False

    # Lock any model case if it has not run yet
    for mcr in mcrs:
        if not mcr.is_used():
            mcr.update_status(config.STATUS_LOCK)

    return True


class ModelLauncher:
    def __init__(self, api: str):
        self.api = api
        self.id = util.generate_md5(api)

        if api not in config.MODEL_REGISTRY:
            raise KeyError(
                f"API '{api}' not found in MODEL_REGISTRY. Available APIs: {list(config.MODEL_REGISTRY.keys())}"
            )

        self.script_path = os.path.join(
            config.DIR_TRIGGER_RESOURCE, config.MODEL_REGISTRY[api]
        )
        self.program_path = os.path.join(
            config.DIR_RESOURCE_MODEL, self.id, get_pyc_filename(self.id)
        )

        compile_model_script_to_pyc(self.api, self.script_path)

        code_obj = load_code_from_pyc(self.program_path)

        local_namespace = {"MCR": MCR, "model": model, "config": config}
        exec(code_obj, local_namespace, local_namespace)

        self.name = (
            local_namespace["NAME"] if "NAME" in local_namespace else "Unknown Name"
        )
        self.category = (
            local_namespace["CATEGORY"]
            if "CATEGORY" in local_namespace
            else "Unknown Category"
        )
        self.category_alias = (
            local_namespace["CATEGORY_ALIAS"]
            if "CATEGORY_ALIAS" in local_namespace
            else "Unknown Category Alias"
        )
        self.parse = (
            types.MethodType(local_namespace["PARSING"], self)
            if "PARSING" in local_namespace
            else lambda: None
        )
        self.response = (
            types.MethodType(local_namespace["RESPONSING"], self)
            if "RESPONSING" in local_namespace
            else lambda: None
        )

    @staticmethod
    def preheat(api: str):
        id = util.generate_md5(api)
        script_path = os.path.join(
            config.DIR_TRIGGER_RESOURCE, config.MODEL_REGISTRY[api]
        )

        compile_model_script_to_pyc(api, script_path)

    def run(self, request_json: dict, other_dependent_ids: list[str] = []) -> MCR:
        other_pre_mcrs = [MCR.open_case(id) for id in other_dependent_ids]
        default_pre_mcrs = self.parse(
            request_json, self.program_path, other_dependent_ids
        )
        mcrs = other_pre_mcrs + default_pre_mcrs

        # Check whether core model case is valid for running
        if mcr_checker(mcrs):
            # Launch model
            command = [self.program_path] + [mcr.id for mcr in mcrs]
            Process_Queue().put(command)

            # Make default response
            self.response(
                core_mcr=default_pre_mcrs[-1],
                default_pre_mcrs=default_pre_mcrs[:-1],
                other_pre_mcrs=other_pre_mcrs,
            )

        return mcrs[-1]

    @staticmethod
    def fetch_model_from_API(api: str):
        return ModelLauncher(api)
