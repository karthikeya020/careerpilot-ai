$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\..\backend"

if (-not (Test-Path ".venv")) {
    $pythonCmd = $null
    foreach ($candidate in @("3.12", "3.11", "3.10")) {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            py "-$candidate" -c "" 2>$null
            if ($?) { $pythonCmd = @("py", "-$candidate"); break }
        }
    }
    if (-not $pythonCmd) { $pythonCmd = @("python") }
    & $pythonCmd[0] $pythonCmd[1] -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend/.env from .env.example -- edit DATABASE_URL/JWT_SECRET as needed."
}

alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
