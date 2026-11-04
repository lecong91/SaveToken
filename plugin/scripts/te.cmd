@echo off
setlocal
set "PYTHONUTF8=1"
set "SCRIPT_DIR=%~dp0"

if defined TE_PYTHON (
    "%TE_PYTHON%" "%SCRIPT_DIR%te_bootstrap.py" cli %*
    exit /b %ERRORLEVEL%
)

where python3 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python3 "%SCRIPT_DIR%te_bootstrap.py" cli %*
    exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%SCRIPT_DIR%te_bootstrap.py" cli %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 "%SCRIPT_DIR%te_bootstrap.py" cli %*
    exit /b %ERRORLEVEL%
)

echo te: Python 3.10+ was not found on PATH. Please install Python or set TE_PYTHON. >&2
exit /b 1
