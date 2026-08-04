#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"

if [ ! -d ".venv" ]; then
  PYBIN=$(command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3 || command -v python)
  "$PYBIN" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example -- edit DATABASE_URL/JWT_SECRET as needed."
fi

alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
