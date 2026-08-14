"""student profile github username

Revision ID: b6e3f81a9c4d
Revises: f4a1c9d02b7e
Create Date: 2026-08-13 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6e3f81a9c4d'
down_revision: Union[str, Sequence[str], None] = 'f4a1c9d02b7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('student_profiles', sa.Column('github_username', sa.String(length=39), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('student_profiles', 'github_username')
