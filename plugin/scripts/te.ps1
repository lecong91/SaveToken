[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$env:PYTHONUTF8 = "1"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Bootstrap = Join-Path $ScriptDir "te_bootstrap.py"

if ($env:TE_PYTHON) {
    & $env:TE_PYTHON $Bootstrap cli @RemainingArgs
    exit $LASTEXITCODE
}

foreach ($cmd in @("python3", "python", "py")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) {
        if ($cmd -eq "py") {
            & py -3 $Bootstrap cli @RemainingArgs
            exit $LASTEXITCODE
        } else {
            & $cmd $Bootstrap cli @RemainingArgs
            exit $LASTEXITCODE
        }
    }
}

Write-Error "te: Python 3.10+ was not found on PATH. Please install Python or set TE_PYTHON."
exit 1
