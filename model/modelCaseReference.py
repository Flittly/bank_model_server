import datetime
import json
import os
import shutil
from typing import Any

import portalocker

import config
import util


class ModelCaseReference:
    def __init__(
        self,
        request_url: str,
        request_json: dict[str, Any],
        model_name: str,
        model_path: str,
        dependent_case_ids: list[str] | None = None,
    ) -> None:
        dependent_case_ids = dependent_case_ids or []
        self.model_name = model_name
        self.model_path = model_path
        self.request_url = request_url
        self.request_json = request_json
        self.dependencies = dependent_case_ids
        self.id = util.generate_md5(
            request_url + json.dumps(request_json, sort_keys=True)
        )
        self.directory = os.path.join(config.DIR_MODEL_CASE, self.id)
        self.local_file_locker = os.path.join(self.directory, "lock")
        self.timestamp = 0

        with open(config.DIR_GLOBALE_FILE_LOCKER, "a+", encoding="utf-8") as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            self.initialize()
            portalocker.unlock(lock_file)

    @staticmethod
    def create(
        request_url: str,
        request_json: dict[str, Any],
        model_name: str,
        model_path: str,
        dependent_case_ids: list[str] | None = None,
    ) -> "ModelCaseReference":
        return ModelCaseReference(
            request_url,
            request_json,
            model_name,
            model_path,
            dependent_case_ids,
        )

    @staticmethod
    def has_case(case_id: str) -> bool:
        return os.path.isdir(os.path.join(config.DIR_MODEL_CASE, case_id))

    @staticmethod
    def open_case(case_id: str) -> "ModelCaseReference | None":
        directory = os.path.join(config.DIR_MODEL_CASE, case_id)
        identity_path = os.path.join(directory, "identity.json")
        if not os.path.exists(identity_path):
            return None

        with open(identity_path, "r", encoding="utf-8") as file:
            identity = json.load(file)

        mcr = ModelCaseReference.__new__(ModelCaseReference)
        mcr.model_name = identity.get("model", "Unknown")
        mcr.model_path = identity.get("model-path", "")
        mcr.request_url = identity.get("url", "")
        mcr.request_json = identity.get("json", {})
        mcr.dependencies = identity.get("dependencies", [])
        mcr.id = case_id
        mcr.directory = directory
        mcr.local_file_locker = os.path.join(directory, "lock")
        mcr.timestamp = ModelCaseReference.get_case_time(case_id)
        return mcr

    @staticmethod
    def check_case_status(case_id: str) -> str:
        mcr = ModelCaseReference.open_case(case_id)
        if mcr is None:
            return "not_found"
        status = mcr.get_status()
        if status & config.STATUS_ERROR:
            return "error"
        if status & config.STATUS_COMPLETE:
            return "completed"
        if status & config.STATUS_RUNNING:
            return "running"
        return "pending"

    @staticmethod
    def get_case_response(case_id: str) -> dict[str, Any] | None:
        response_path = os.path.join(config.DIR_MODEL_CASE, case_id, "response.json")
        if not os.path.exists(response_path):
            return None
        with open(response_path, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def get_status_log(case_id: str) -> str | None:
        directory = os.path.join(config.DIR_MODEL_CASE, case_id, "status")
        if not os.path.isdir(directory):
            return None
        filenames = util.get_filenames(directory)
        if not filenames:
            return None
        with open(os.path.join(directory, filenames[0]), "r", encoding="utf-8") as file:
            return file.read().strip()

    @staticmethod
    def get_simplified_error_log(case_id: str) -> str:
        return (
            ModelCaseReference.get_status_log(case_id)
            or "Unknown model execution error"
        )

    @staticmethod
    def get_pre_error_cases(case_id: str) -> list[str]:
        error_log = ModelCaseReference.get_status_log(case_id)
        if not error_log:
            return []
        return [value for value in error_log.splitlines()[0].split("-") if value]

    @staticmethod
    def delete_case(case_id: str) -> bool:
        directory = os.path.join(config.DIR_MODEL_CASE, case_id)
        if not os.path.isdir(directory):
            return False
        shutil.rmtree(directory)
        return True

    @staticmethod
    def is_case_locked(case_id: str) -> bool | None:
        mcr = ModelCaseReference.open_case(case_id)
        if mcr is None:
            return None
        return mcr.find_status(config.STATUS_LOCK)

    @staticmethod
    def get_case_time(case_id: str) -> int:
        directory = os.path.join(config.DIR_MODEL_CASE, case_id, "time")
        if not os.path.isdir(directory):
            return 0
        filenames = util.get_filenames(directory)
        if not filenames:
            return 0
        return int(filenames[0])

    @staticmethod
    def generate_pre_error_log(core_case_id: str, error_case_ids: list[str]) -> str:
        return "-".join(error_case_ids)

    @staticmethod
    def is_case_done(case_id: str) -> bool:
        mcr = ModelCaseReference.open_case(case_id)
        if mcr is None:
            return True
        status = mcr.get_status()
        return bool(status & config.STATUS_COMPLETE or status & config.STATUS_ERROR)

    @staticmethod
    def update_case_status(
        case_id: str,
        status: int,
        content: str | None = None,
        mode: str = "a",
    ) -> None:
        mcr = ModelCaseReference.open_case(case_id)
        if mcr is not None:
            mcr.update_status(status, content, mode)

    def initialize(self) -> None:
        if os.path.exists(self.directory):
            return

        os.makedirs(self.directory, exist_ok=True)
        with open(self.local_file_locker, "a+", encoding="utf-8") as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            os.makedirs(os.path.join(self.directory, "time"), exist_ok=True)
            os.makedirs(os.path.join(self.directory, "result"), exist_ok=True)
            os.makedirs(os.path.join(self.directory, "status"), exist_ok=True)

            with open(
                os.path.join(self.directory, "identity.json"), "w", encoding="utf-8"
            ) as file:
                json.dump(
                    {
                        "model": self.model_name,
                        "model-path": self.model_path,
                        "url": self.request_url,
                        "json": self.request_json,
                        "dependencies": self.dependencies,
                    },
                    file,
                    indent=4,
                )

            with open(
                os.path.join(self.directory, "status", str(config.STATUS_UNLOCK)),
                "w",
                encoding="utf-8",
            ) as file:
                file.write("OK")

            self.make_response({})
            self.update_call_time()
            portalocker.unlock(lock_file)

    def update_call_time(self) -> None:
        time_directory = os.path.join(self.directory, "time")
        os.makedirs(time_directory, exist_ok=True)
        current_timestamp = int(datetime.datetime.now().timestamp() * 1000)
        for filename in util.get_filenames(time_directory):
            os.remove(os.path.join(time_directory, filename))
        with open(
            os.path.join(time_directory, str(current_timestamp)), "w", encoding="utf-8"
        ):
            pass
        self.timestamp = current_timestamp

    def get_status(self) -> int:
        status_directory = os.path.join(self.directory, "status")
        filenames = util.get_filenames(status_directory)
        if not filenames:
            return config.STATUS_NONE
        return int(filenames[0])

    def update_status(self, status: int, content: Any = None, mode: str = "a") -> None:
        with open(self.local_file_locker, "a+", encoding="utf-8") as lock_file:
            portalocker.lock(lock_file, portalocker.LOCK_EX)
            status_directory = os.path.join(self.directory, "status")
            filenames = util.get_filenames(status_directory)
            current_status = int(filenames[0]) if filenames else config.STATUS_NONE

            if current_status != status:
                if filenames:
                    os.remove(os.path.join(status_directory, filenames[0]))
                with open(
                    os.path.join(status_directory, str(status)), "w", encoding="utf-8"
                ) as file:
                    if content is not None:
                        file.write(f"{content}\n")
                    else:
                        file.write("OK")
            elif content is not None:
                with open(
                    os.path.join(status_directory, str(status)), mode, encoding="utf-8"
                ) as file:
                    file.write(f"{content}\n")

            self.update_call_time()
            portalocker.unlock(lock_file)

    def find_status(self, status_flag: int) -> bool:
        return (self.get_status() & status_flag) != 0

    def is_used(self) -> bool:
        return self.find_status(config.STATUS_LOCK) or self.find_status(
            config.STATUS_RUNNING
        )

    def make_response(
        self, content: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        response_path = os.path.join(self.directory, "response.json")
        if content is None:
            if not os.path.exists(response_path):
                return None
            with open(response_path, "r", encoding="utf-8") as file:
                return json.load(file)

        current_response = {}
        if os.path.exists(response_path):
            with open(response_path, "r", encoding="utf-8") as file:
                current_response = json.load(file)

        current_response.update(content)
        current_response["case-id"] = self.id
        current_response["model"] = self.model_name

        with open(response_path, "w", encoding="utf-8") as file:
            json.dump(current_response, file, indent=4)

        return current_response

    def result_packaging(self) -> str:
        result_directory = os.path.join(self.directory, "result")
        archive_without_extension = os.path.join(self.directory, "result")
        util.create_zip_from_folder(result_directory, archive_without_extension)
        return archive_without_extension + ".zip"
