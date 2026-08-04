# Database

The authoritative Phase 1 schema is managed via **Alembic migrations** in
`backend/alembic/versions/` (co-located with the SQLAlchemy models in
`backend/app/models/`, which is the standard layout for a SQLAlchemy+Alembic
project). Run `alembic upgrade head` from `backend/` (or use
`scripts/migrate.ps1` / `scripts/migrate.sh`) to create or update the schema.

`schema.sql` in this directory is the original Phase 0 blueprint draft. It
predates the implemented Phase 1 data model (different table names and a
narrower set of entities) and is kept only for historical reference — it is
**not** applied anywhere and does not reflect the current schema. Reference
data (the five RBAC roles and the skill taxonomy) is seeded by a dedicated
Alembic data migration, not by a raw SQL file; the demo student is seeded
separately by `python -m app.seed.seed_demo`.
