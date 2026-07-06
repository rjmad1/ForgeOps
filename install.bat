@echo off
setlocal enabledelayedexpansion

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Administrator privileges confirmed.
) else (
    echo [INFO] Requesting Administrator privileges...
    powershell -Command "Start-Process -FilePath '%comspec%' -ArgumentList '/c \"\"%~dpnx0\"\"' -Verb RunAs"
    exit /b
)

:: Set current directory to the location of the script
cd /d "%~dp0"
echo ===================================================
echo   AI Control Plane Version 1.0 Installer
echo ===================================================
echo.

:: Detect Python
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Python was not found in PATH.
    echo [INFO] Attempting to install Python 3.11 via winget...
    winget install --id Python.Python.3.11 --exact --silent --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install Python via winget. Please install Python 3.10+ manually.
        pause
        exit /b 1
    )
    :: Refresh PATH for the current session
    set "PATH=%PATH%;%USERPROFILE%\AppData\Local\Programs\Python\Python311;%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts"
)

:: Check Python version (should be 3.10+)
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
if %errorLevel% neq 0 (
    echo [ERROR] Python version must be 3.10 or higher.
    pause
    exit /b 1
)

:: Initialize python virtual environment
if not exist .venv (
    echo [INFO] Creating virtual environment in .venv...
    python -m venv .venv
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Install dependencies
echo [INFO] Installing required dependencies...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install dependencies from requirements.txt.
    pause
    exit /b 1
)

:: Execute the core Python installer
echo [INFO] Running installer logic...
.venv\Scripts\python scripts\install.py
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Installation failed. Check errors above.
    pause
    exit /b 1
)

echo.
echo [INFO] Installation completed successfully.
echo.
pause
