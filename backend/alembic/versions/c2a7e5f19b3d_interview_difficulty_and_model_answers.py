"""interview difficulty and model answers

Revision ID: c2a7e5f19b3d
Revises: b6e3f81a9c4d
Create Date: 2026-08-13 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2a7e5f19b3d'
down_revision: Union[str, Sequence[str], None] = 'b6e3f81a9c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('interview_questions', sa.Column('difficulty', sa.String(length=10), server_default='medium', nullable=False))
    op.add_column('interview_questions', sa.Column('model_answer_summary', sa.Text(), server_default='', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('interview_questions', 'model_answer_summary')
    op.drop_column('interview_questions', 'difficulty')
