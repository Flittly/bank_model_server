import os

# Set PROJ_LIB to empty string to avoid conflicts with other PROJ installations (e.g. PostGIS)
os.environ["PROJ_LIB"] = ""

import config
from model import launcher
from app import create_app
from util import StorageMonitor
import uvicorn


def initialize_work_space():
    os.makedirs(config.DIR_MODEL_CASE, exist_ok=True)
    os.makedirs(os.path.dirname(config.DIR_STORAGE_LOG), exist_ok=True)

    if not os.path.exists(config.DIR_GLOBALE_FILE_LOCKER):
        with open(config.DIR_GLOBALE_FILE_LOCKER, "w") as file:
            pass

    if not os.path.exists(config.DIR_STORAGE_LOG):
        with open(config.DIR_STORAGE_LOG, "w", encoding="utf-8") as file:
            file.write("0\n")

    for key in config.MODEL_REGISTRY:
        launcher.preheat(key)

    StorageMonitor().initialize([config.DIR_ROOT], config.DIR_STORAGE_LOG)


if __name__ == "__main__":
    # Set PROJ_LIB environment variable to use the proj data from the venv
    import sys

    if sys.platform == "win32":
        venv_path = os.path.dirname(sys.executable)
        proj_lib = os.path.join(venv_path, "Library", "share", "proj")
        if not os.path.exists(proj_lib):
            # check alternative location for standard python install/uv
            proj_lib = os.path.join(venv_path, "..", "share", "proj")

        # Fallback to checking site-packages if not found in Library/share/proj
        if not os.path.exists(proj_lib):
            import site

            site_packages = site.getsitepackages()[
                0
            ]  # usually the first one is the venv site-packages
            proj_lib = os.path.join(site_packages, "osgeo", "data", "proj")

        if os.path.exists(proj_lib):
            os.environ["PROJ_LIB"] = proj_lib
            print(f"Set PROJ_LIB to: {proj_lib}")

    initialize_work_space()

    app = create_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.APP_PORT,
        log_level="debug" if config.APP_DEBUG else "info",
    )
