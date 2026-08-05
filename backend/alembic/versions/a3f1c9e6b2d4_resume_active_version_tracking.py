"""resume active version tracking

Revision ID: a3f1c9e6b2d4
Revises: 074b58839c25
Create Date: 2026-08-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f1c9e6b2d4'
down_revision: Union[str, Sequence[str], None] = '074b58839c25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default backfills existing rows (every resume defaults to
    # active=True) before the NOT NULL constraint applies -- required against
    # a non-empty Postgres table.
    with op.batch_alter_table('resumes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column('superseded_at', sa.DateTime(), nullable=True))

    # Data backfill: the server_default above makes every existing resume
    # "active", which would violate the single-active-resume-per-student
    # invariant for any student who already has more than one resume row.
    # Immediately re-establish the invariant: only each student's most
    # recently uploaded resume stays active; earlier ones are marked
    # superseded now. Window functions are supported by both the Postgres
    # runtime and the SQLite test/dev fallback.
    op.execute(
        """
        UPDATE resumes
        SET is_active = false, superseded_at = CURRENT_TIMESTAMP
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY student_profile_id ORDER BY uploaded_at DESC
                ) AS rn
                FROM resumes
            ) ranked
            WHERE rn = 1
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('resumes', schema=None) as batch_op:
        batch_op.drop_column('superseded_at')
        batch_op.drop_column('is_active')
