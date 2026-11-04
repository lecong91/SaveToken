<#
.SYNOPSIS
    SaveToken 1-Click Installer for Windows (PowerShell)
#>
[CmdletBinding()]
param()

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SaveToken 1-Click Installer for Windows (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$InstallerScript = Join-Path $ScriptDir "scripts\install_antigravity.py"

$pythonCmd = $null
foreach ($cmd in @("python", "py", "python3")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) {
        $pythonCmd = $cmd
        break
    }
}

if (-not $pythonCmd) {
    Write-Error "[ERROR] Python 3.10+ was not found on PATH. Please install Python from https://www.python.org/ or check your PATH."
    exit 1
}

if ($pythonCmd -eq "py") {
    & py -3 $InstallerScript
} else {
    & $pythonCmd $InstallerScript
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nInstallation completed successfully." -ForegroundColor Green
} else {
    Write-Host "`nInstallation failed with code $LASTEXITCODE." -ForegroundColor Red
}
exit $LASTEXITCODE
