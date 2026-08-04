"""seed reference roles and skills

Revision ID: 2e021960668e
Revises: 788d1325f003
Create Date: 2026-08-04 10:46:12.850339

"""
import sys
import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa

from alembic import op

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.core.types import GUID, JSONBType
from app.models.user import ALL_ROLES
from app.seed.skills_taxonomy import SKILLS

# revision identifiers, used by Alembic.
revision: str = '2e021960668e'
down_revision: str | Sequence[str] | None = '788d1325f003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upgrade() -> None:
    # Column types here must match the real model column types (GUID /
    # JSONBType), not generic sa.String()/sa.JSON() -- on SQLite the loose
    # typing hides a mismatch, but Postgres' native `uuid` column rejects an
    # implicit VARCHAR bind during bulk_insert.
    roles_table = sa.table(
        "roles",
        sa.column("id", GUID()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
    )
    skills_table = sa.table(
        "skills",
        sa.column("id", GUID()),
        sa.column("name", sa.String()),
        sa.column("category", sa.String()),
        sa.column("aliases", JSONBType()),
        sa.column("description", sa.String()),
        sa.column("created_at", sa.DateTime()),
    )

    op.bulk_insert(
        roles_table,
        [
            {"id": str(uuid.uuid4()), "name": role, "description": f"{role.replace('_', ' ').title()} role"}
            for role in ALL_ROLES
        ],
    )
    op.bulk_insert(
        skills_table,
        [
            {
                "id": str(uuid.uuid4()),
                "name": skill["name"],
                "category": skill["category"],
                "aliases": skill["aliases"],
                "description": "",
                "created_at": _now(),
            }
            for skill in SKILLS
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM skills")
    op.execute("DELETE FROM roles")
