"""student profile assessment goal

Adds `student_profiles.assessment_goal` -- the free-text placement goal the
student types into the Assessment "daily goal" bar. Purely additive.

Revision ID: c3d9b1f6a482
Revises: fa1c8e4b7d20
Create Date: 2026-09-02 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d9b1f6a482"
down_revision: Union[str, Sequence[str], None] = "fa1c8e4b7d20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("student_profiles", sa.Column("assessment_goal", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("student_profiles", "assessment_goal")
