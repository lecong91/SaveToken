@echo off
setlocal
set "PYTHONUTF8=1"
set "SCRIPT_DIR=%~dp0"

if defined TE_PYTHON (
    "%TE_PYTHON%" "%SCRIPT_DIR%antigravity_hook.py" %*
    exit /b %ERRORLEVEL%
)

where python3 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python3 "%SCRIPT_DIR%antigravity_hook.py" %*
    exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%SCRIPT_DIR%antigravity_hook.py" %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 "%SCRIPT_DIR%antigravity_hook.py" %*
    exit /b %ERRORLEVEL%
)

echo {"error": "Python 3.10+ not found on PATH"}
exit /b 1
