"""leetcode completions

Creates `leetcode_completions` -- the LeetCode problems a student has marked
done from the practice plan, plus the optional pasted code and its AI review.

Revision ID: d8e2a5c74f19
Revises: c3d9b1f6a482
Create Date: 2026-09-02 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.types import GUID, JSONBType

# revision identifiers, used by Alembic.
revision: str = "d8e2a5c74f19"
down_revision: Union[str, Sequence[str], None] = "c3d9b1f6a482"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leetcode_completions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("student_profile_id", GUID(), nullable=False),
        sa.Column("problem_slug", sa.String(length=160), nullable=False),
        sa.Column("problem_title", sa.String(length=200), nullable=False),
        sa.Column("difficulty", sa.String(length=10), server_default="", nullable=False),
        sa.Column("concept_slug", sa.String(length=80), nullable=True),
        sa.Column("domain_slug", sa.String(length=50), nullable=True),
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=30), nullable=True),
        sa.Column("analysis", JSONBType(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_profile_id", "problem_slug", name="uq_leetcode_completion_student_slug"),
    )
    op.create_index(
        "ix_leetcode_completions_student_profile_id", "leetcode_completions", ["student_profile_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_leetcode_completions_student_profile_id", table_name="leetcode_completions")
    op.drop_table("leetcode_completions")
