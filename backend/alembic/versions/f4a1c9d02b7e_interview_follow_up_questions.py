"""interview follow-up questions

Revision ID: f4a1c9d02b7e
Revises: ebab97440c22
Create Date: 2026-08-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import app.core.types


# revision identifiers, used by Alembic.
revision: str = 'f4a1c9d02b7e'
down_revision: Union[str, Sequence[str], None] = 'ebab97440c22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('interview_questions', sa.Column('is_follow_up', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('interview_questions', sa.Column('parent_question_id', app.core.types.GUID(), nullable=True))
    op.add_column('interview_questions', sa.Column('follow_up_rationale', sa.Text(), nullable=True))
    with op.batch_alter_table('interview_questions', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_interview_questions_parent_question_id',
            'interview_questions',
            ['parent_question_id'],
            ['id'],
            ondelete='CASCADE',
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('interview_questions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_interview_questions_parent_question_id', type_='foreignkey')
    op.drop_column('interview_questions', 'follow_up_rationale')
    op.drop_column('interview_questions', 'parent_question_id')
    op.drop_column('interview_questions', 'is_follow_up')
