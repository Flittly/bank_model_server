@echo off
echo Starting Bank Model Server...

REM Check if uv is available
where uv >nul 2>&1
if %errorlevel% equ 0 (
    echo Using uv to run the server...
    uv run python run.py
) else (
    echo uv not found, using pip...
    pip install -r requirements.txt
    python run.py
)

pause