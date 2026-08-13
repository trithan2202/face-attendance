$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Python virtual environment not found. Run: py -m venv .venv, then .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

& ".venv\Scripts\python.exe" -m scripts.bootstrap_db
