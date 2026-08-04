from datetime import datetime, timezone

UTC = timezone.utc

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.redis_client import get_redis
from app.graphrag.neo4j_client import is_graph_available

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


@router.get("/health/dependencies")
def dependency_health_check(db: Session = Depends(get_db)) -> dict[str, str | bool | dict]:
    """Consolidated dependency-health status for every backing service --
    database, Redis, and Neo4j -- each independently checked so one
    dependency's outage never masks another's status. Every dependency in
    this codebase already degrades gracefully on its own (deterministic AI
    provider, relational GraphRAG fallback, fail-open rate limiting); this
    endpoint exists so that degraded state is externally observable, not
    just internally tolerated."""
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        redis_ok = bool(get_redis().ping())
    except Exception:
        redis_ok = False

    neo4j_ok = is_graph_available()

    dependencies = {"database": db_ok, "redis": redis_ok, "neo4j": neo4j_ok}
    all_ok = all(dependencies.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "dependencies": dependencies,
        "timestamp": datetime.now(UTC).isoformat(),
    }
