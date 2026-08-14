"""job catalog schema and seed

Creates the Company Job Catalog tables (reference data, like
assessment_domains/skills) and seeds them with the curated listings in
app/seed/company_job_catalog.py. The `assessment_attempts` / etc.
FK-recreate diffs that `alembic revision --autogenerate` also proposed here
are dropped from this migration -- SQLite autogenerate noise against the
local dev DB (it doesn't preserve named FK constraint metadata the same way
Postgres does), not a real model change; those tables are untouched.

Revision ID: 6181bfa011a8
Revises: 190e57633512
Create Date: 2026-08-06 03:40:45.176417

"""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.core.types
from app.core.types import GUID, JSONBType

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.seed.company_job_catalog import LISTINGS  # noqa: E402

# revision identifiers, used by Alembic.
revision: str = '6181bfa011a8'
down_revision: Union[str, Sequence[str], None] = '190e57633512'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upgrade() -> None:
    op.create_table(
        'company_job_listings',
        sa.Column('company', sa.String(length=150), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('sector', sa.String(length=30), nullable=False),
        sa.Column('seniority', sa.String(length=50), nullable=False),
        sa.Column('package_min_lpa', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('package_max_lpa', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('emphasis_domains', app.core.types.JSONBType(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('id', app.core.types.GUID(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('company_job_listings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_company_job_listings_company'), ['company'], unique=False)
        batch_op.create_index(batch_op.f('ix_company_job_listings_sector'), ['sector'], unique=False)

    op.create_table(
        'job_listing_requirements',
        sa.Column('listing_id', app.core.types.GUID(), nullable=False),
        sa.Column('skill_id', app.core.types.GUID(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('id', app.core.types.GUID(), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['company_job_listings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('job_listing_requirements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_listing_requirements_listing_id'), ['listing_id'], unique=False)

    op.create_table(
        'tracked_jobs',
        sa.Column('student_profile_id', app.core.types.GUID(), nullable=False),
        sa.Column('listing_id', app.core.types.GUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('id', app.core.types.GUID(), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['company_job_listings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_profile_id', 'listing_id', name='uq_tracked_job_student_listing'),
    )
    with op.batch_alter_table('tracked_jobs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tracked_jobs_listing_id'), ['listing_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_tracked_jobs_student_profile_id'), ['student_profile_id'], unique=False)

    # ---- seed the curated catalog ----
    bind = op.get_bind()
    listings_table = sa.table(
        'company_job_listings',
        sa.column('id', GUID()), sa.column('company', sa.String()), sa.column('title', sa.String()),
        sa.column('sector', sa.String()), sa.column('seniority', sa.String()),
        sa.column('package_min_lpa', sa.Numeric()), sa.column('package_max_lpa', sa.Numeric()),
        sa.column('description', sa.String()), sa.column('emphasis_domains', JSONBType()),
        sa.column('created_at', sa.DateTime()),
    )
    requirements_table = sa.table(
        'job_listing_requirements',
        sa.column('id', GUID()), sa.column('listing_id', GUID()), sa.column('skill_id', GUID()),
        sa.column('is_required', sa.Boolean()),
    )
    skills_table = sa.table('skills', sa.column('id', GUID()), sa.column('name', sa.String()))
    skill_id_by_name = {row.name: row.id for row in bind.execute(sa.select(skills_table.c.id, skills_table.c.name))}

    listing_rows = []
    requirement_rows = []
    for listing in LISTINGS:
        listing_id = uuid.uuid4()
        listing_rows.append(
            {
                "id": str(listing_id), "company": listing["company"], "title": listing["title"],
                "sector": listing["sector"], "seniority": listing["seniority"],
                "package_min_lpa": listing["package_min"], "package_max_lpa": listing["package_max"],
                "description": listing["description"], "emphasis_domains": listing["emphasis_domains"],
                "created_at": _now(),
            }
        )
        for skill_name in listing["required_skills"]:
            requirement_rows.append(
                {"id": str(uuid.uuid4()), "listing_id": str(listing_id), "skill_id": str(skill_id_by_name[skill_name]), "is_required": True}
            )
        for skill_name in listing["optional_skills"]:
            requirement_rows.append(
                {"id": str(uuid.uuid4()), "listing_id": str(listing_id), "skill_id": str(skill_id_by_name[skill_name]), "is_required": False}
            )

    op.bulk_insert(listings_table, listing_rows)
    op.bulk_insert(requirements_table, requirement_rows)


def downgrade() -> None:
    op.drop_table('tracked_jobs')
    op.drop_table('job_listing_requirements')
    op.drop_table('company_job_listings')
