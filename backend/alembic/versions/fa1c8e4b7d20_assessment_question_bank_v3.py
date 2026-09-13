"""assessment question bank v3 (hard concept + implementation questions)

Adds difficulty 4-5 questions to the ALREADY-SEEDED assessment domains
(sql, python, javascript, dsa, oop, java) and their existing concepts.
Purely additive: every question is referenced by (domain_slug, concept_slug)
and its concept_id is looked up from the DB at upgrade time -- this migration
never creates a domain or concept and never edits a row from an earlier
migration. Mirrors the "extra questions on existing concepts" step of
190e57633512_expand_assessment_question_bank_v2.

Revision ID: fa1c8e4b7d20
Revises: e7c4a9d2f1b8
Create Date: 2026-09-01 00:20:00.000000

"""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.types import GUID, JSONBType

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.seed.assessment_taxonomy import BANK_V3_QUESTIONS  # noqa: E402

# revision identifiers, used by Alembic.
revision: str = "fa1c8e4b7d20"
down_revision: Union[str, Sequence[str], None] = "e7c4a9d2f1b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upgrade() -> None:
    bind = op.get_bind()

    domains_table = sa.table("assessment_domains", sa.column("id", GUID()), sa.column("slug", sa.String()))
    concepts_table = sa.table(
        "concepts", sa.column("id", GUID()), sa.column("domain_id", GUID()), sa.column("slug", sa.String())
    )
    questions_table = sa.table(
        "questions",
        sa.column("id", GUID()), sa.column("domain_id", GUID()), sa.column("concept_id", GUID()),
        sa.column("question_type", sa.String()), sa.column("prompt", sa.String()),
        sa.column("options", JSONBType()), sa.column("correct_answer", JSONBType()),
        sa.column("explanation", sa.String()), sa.column("difficulty", sa.Integer()),
        sa.column("target_role_relevance", JSONBType()), sa.column("created_at", sa.DateTime()),
    )

    domain_id_by_slug = {
        row.slug: row.id for row in bind.execute(sa.select(domains_table.c.id, domains_table.c.slug))
    }
    domain_slug_by_id = {v: k for k, v in domain_id_by_slug.items()}
    concept_id_by_key: dict[tuple[str, str], object] = {}
    for row in bind.execute(
        sa.select(concepts_table.c.id, concepts_table.c.domain_id, concepts_table.c.slug)
    ):
        domain_slug = domain_slug_by_id.get(row.domain_id)
        if domain_slug:
            concept_id_by_key[(domain_slug, row.slug)] = row.id

    rows = []
    for q in BANK_V3_QUESTIONS:
        key = (q["domain"], q["concept"])
        if key not in concept_id_by_key:
            raise RuntimeError(f"bank_v3: no seeded concept for {key} -- expected an existing domain/concept")
        rows.append(
            {
                "id": str(uuid.uuid4()),
                "domain_id": str(domain_id_by_slug[q["domain"]]),
                "concept_id": str(concept_id_by_key[key]),
                "question_type": q["question_type"],
                "prompt": q["prompt"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"],
                "difficulty": q["difficulty"],
                "target_role_relevance": q["target_role_relevance"],
                "created_at": _now(),
            }
        )
    op.bulk_insert(questions_table, rows)


def downgrade() -> None:
    questions_table = sa.table("questions", sa.column("prompt", sa.String()))
    prompts = [q["prompt"] for q in BANK_V3_QUESTIONS]
    if prompts:
        op.execute(questions_table.delete().where(questions_table.c.prompt.in_(prompts)))
