@echo off
setlocal
echo ============================================================
echo  SaveToken 1-Click Installer for Windows (Command Prompt)
echo ============================================================

set "SCRIPT_DIR=%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%SCRIPT_DIR%scripts\install_antigravity.py"
    goto :done
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 "%SCRIPT_DIR%scripts\install_antigravity.py"
    goto :done
)

where python3 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python3 "%SCRIPT_DIR%scripts\install_antigravity.py"
    goto :done
)

echo [ERROR] Python 3.10+ was not found on PATH.
echo Please install Python from https://www.python.org/ or enable it in your Environment Variables.
exit /b 1

:done
echo Installation process finished.
exit /b 0
