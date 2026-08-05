FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# setuptools pinned >=78.1.1: the python:3.12-slim base image ships an older
# setuptools with several known CVEs (path traversal / RCE in its package-
# index download path -- CVE-2024-6345, CVE-2025-47273); none are reachable
# through this app's own request-handling code, but there is no reason to
# ship a vulnerable version when upgrading costs nothing. See pip-audit
# findings in docs/security/SECURITY_REVIEW.md.
RUN pip install --upgrade pip "setuptools>=78.1.1" && pip install .

EXPOSE 8000

# Run migrations, mirror the relational taxonomy into the graph store
# (idempotent MERGE-based, exits 0 and logs a message if Neo4j isn't
# reachable rather than blocking startup) *before* seeding the demo student,
# so the demo student's root-cause trace is graph-sourced from the very
# first boot instead of falling back for one run, then start the API.
# Reference data (roles + skill taxonomy) is seeded by the migrations
# themselves. This makes "restart the backend container" a genuine
# one-click demo reset with no manual `docker compose exec` step required
# before a presentation.
CMD ["sh", "-c", "alembic upgrade head && python -m app.graphrag.run_seed && python -m app.seed.seed_demo && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
