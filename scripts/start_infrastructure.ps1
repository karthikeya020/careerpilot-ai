$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."
docker compose up -d postgres redis neo4j
docker compose ps
