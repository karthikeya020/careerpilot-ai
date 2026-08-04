$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\frontend"

if (-not (Test-Path "node_modules")) {
    npm install
}
if (-not (Test-Path ".env.local")) {
    Copy-Item ".env.local.example" ".env.local"
}
npm run dev
