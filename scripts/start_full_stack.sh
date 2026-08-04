#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Building and starting the full stack (postgres, redis, neo4j, backend, frontend) in Docker..."
docker compose up --build
