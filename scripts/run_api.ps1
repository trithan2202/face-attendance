$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Python virtual environment not found. Run: py -m venv .venv, then .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

& ".venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
