@echo off
setlocal

:: Ensure we run from repo root
cd /d "%~dp0"

:: Create venv if missing
if not exist "venv" (
    echo [setup] Creating virtual environment...
    py -m venv venv
    if %errorlevel% neq 0 goto :error
)

:: Activate venv
call .\venv\Scripts\activate.bat
if %errorlevel% neq 0 goto :error

:: Install dependencies (idempotent)
echo [setup] Installing/ensuring dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 goto :error

:: Backend + UI configuration
if "%BACKEND_PORT%"=="" set BACKEND_PORT=8000
if "%BACKEND_URL%"=="" set BACKEND_URL=http://localhost:%BACKEND_PORT%

set STREAMLIT_BROWSER_GAP=0
set STREAMLIT_SERVER_PORT=8501
set STREAMLIT_SERVER_HEADLESS=true

echo [run] Starting backend (FastAPI) on %BACKEND_URL% ...
start "ContentAlchemy API" cmd /k "cd /d %~dp0 && call .\venv\Scripts\activate.bat && set BACKEND_API_KEY=%BACKEND_API_KEY% && set BACKEND_PORT=%BACKEND_PORT% && uvicorn src.api.server:app --host 0.0.0.0 --port %BACKEND_PORT%"

echo [run] Starting Streamlit UI pointing to backend %BACKEND_URL% ...
start "ContentAlchemy UI" cmd /k "cd /d %~dp0 && call .\venv\Scripts\activate.bat && set BACKEND_URL=%BACKEND_URL% && set BACKEND_API_KEY=%BACKEND_API_KEY% && streamlit run app.py"

goto :eof

:error
echo [error] Command failed with code %errorlevel%.
endlocal & exit /b %errorlevel%

:eof
endlocal
