import os
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture()
def migrated_engine(tmp_path):
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = db_url
    try:
        cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        command.upgrade(cfg, "head")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(migrated_engine):
    session_factory = sessionmaker(bind=migrated_engine, autoflush=False, autocommit=False)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def client(migrated_engine):
    from app.core.db import get_db
    from app.core.rate_limit import login_rate_limiter, register_rate_limiter
    from app.main import app

    session_factory = sessionmaker(bind=migrated_engine, autoflush=False, autocommit=False)

    def _override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    # Real IP-keyed rate limits would throttle the suite itself (it
    # registers/logs in far more than 10 times/minute from one TestClient
    # "IP") -- disabled here the same way get_db is overridden, not by
    # weakening the limiter itself.
    app.dependency_overrides[login_rate_limiter] = lambda: None
    app.dependency_overrides[register_rate_limiter] = lambda: None
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
