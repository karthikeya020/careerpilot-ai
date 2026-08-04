$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."
Write-Host "Building and starting the full stack (postgres, redis, neo4j, backend, frontend) in Docker..."
docker compose up --build
