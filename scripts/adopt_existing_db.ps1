$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Chưa có môi trường .venv. Hãy tạo và cài requirements.txt trước."
}

Write-Host "Chỉ dùng script này nếu 5 bảng cũ đã được tạo bằng scripts/init_db.py."
& ".venv\Scripts\python.exe" -m alembic stamp 20260813_0001
& ".venv\Scripts\python.exe" -m alembic upgrade head
& ".venv\Scripts\python.exe" -m scripts.seed_admin
