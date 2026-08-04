$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"
& .\.venv\Scripts\Activate.ps1
python -m app.seed.seed_demo
