"""student profile leetcode username

Revision ID: e7c4a9d2f1b8
Revises: c2a7e5f19b3d
Create Date: 2026-09-01 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7c4a9d2f1b8'
down_revision: Union[str, Sequence[str], None] = 'c2a7e5f19b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('student_profiles', sa.Column('leetcode_username', sa.String(length=64), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('student_profiles', 'leetcode_username')
