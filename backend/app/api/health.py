from datetime import datetime, timezone

UTC = timezone.utc

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "careerpilot-api",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict[str, str | bool]:
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "timestamp": datetime.now(UTC).isoformat(),
    }
