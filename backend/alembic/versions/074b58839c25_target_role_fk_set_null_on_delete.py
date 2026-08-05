"""cross-reference FKs set null on delete

Revision ID: 074b58839c25
Revises: 957a79bda179
Create Date: 2026-08-05 08:41:07.734753

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '074b58839c25'
down_revision: str | Sequence[str] | None = '957a79bda179'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, column, constraint_name, referenced_table)
_FK_FIXES = [
    ("interview_sessions", "target_role_id", "interview_sessions_target_role_id_fkey", "target_roles"),
    ("experiment_scenarios", "target_role_id", "experiment_scenarios_target_role_id_fkey", "target_roles"),
    ("assessment_attempts", "target_role_id", "assessment_attempts_target_role_id_fkey", "target_roles"),
    ("interview_sessions", "job_description_id", "interview_sessions_job_description_id_fkey", "job_descriptions"),
    ("interview_evaluations", "care_execution_id", "interview_evaluations_care_execution_id_fkey", "care_executions"),
    (
        "career_twin_snapshots",
        "previous_snapshot_id",
        "career_twin_snapshots_previous_snapshot_id_fkey",
        "career_twin_snapshots",
    ),
    (
        "experiment_results",
        "baseline_snapshot_id",
        "experiment_results_baseline_snapshot_id_fkey",
        "career_twin_snapshots",
    ),
]


def upgrade() -> None:
    """Upgrade schema.

    Seven cross-reference foreign keys had no ON DELETE behavior: each
    points from one student-scoped table to another (e.g.
    interview_sessions.target_role_id -> target_roles.id,
    experiment_results.baseline_snapshot_id -> career_twin_snapshots.id),
    where both sides are deleted together whenever a student account is
    deleted, via independent cascade paths from student_profiles. Without an
    explicit ON DELETE clause, Postgres raised a ForeignKeyViolation
    whenever the referenced row's cascade delete was issued before the
    referencing row's -- caught live only once the demo-seed reset deleted
    and recreated a demo student that had real interview/experiment/twin
    history (a fresh account with no such rows never exercised this path).
    None of these seven represent data that should block a delete or that
    needs to be destroyed alongside its target -- SET NULL on all seven
    matches the precedent already set by student_profiles.
    primary_target_role_id and audit_events' nullable FKs.

    Postgres-only: these seven constraints were created with Postgres's
    default `{table}_{column}_fkey` naming, which SQLite (used by the test
    suite) never reflects as a named constraint to begin with -- and
    SQLite's test connections don't enable `PRAGMA foreign_keys` in this
    project, so no ON DELETE behavior is enforced there regardless. Running
    this migration's constraint rename against SQLite would fail on a
    "no such constraint" lookup for a name that dialect never assigned.
    """
    if op.get_bind().dialect.name != "postgresql":
        return
    for table, column, constraint, referenced_table in _FK_FIXES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(constraint, type_="foreignkey")
            batch_op.create_foreign_key(constraint, referenced_table, [column], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name != "postgresql":
        return
    for table, column, constraint, referenced_table in reversed(_FK_FIXES):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(constraint, type_="foreignkey")
            batch_op.create_foreign_key(constraint, referenced_table, [column], ["id"])
