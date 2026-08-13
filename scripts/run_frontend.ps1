$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $projectRoot "frontend")

if (-not (Test-Path "node_modules")) {
    throw "Chưa cài frontend dependencies. Hãy chạy npm install trong thư mục frontend."
}

npm run dev
