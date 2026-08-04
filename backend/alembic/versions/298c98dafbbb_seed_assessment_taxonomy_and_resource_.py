"""seed assessment taxonomy and resource catalog

Revision ID: 298c98dafbbb
Revises: 2d1305695e6c
Create Date: 2026-08-04 17:18:36.154607

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
from app.seed.assessment_taxonomy import CONCEPT_DEPENDENCIES, CONCEPTS, DOMAINS, QUESTIONS, RESOURCES  # noqa: E402

# revision identifiers, used by Alembic.
revision: str = '298c98dafbbb'
down_revision: Union[str, Sequence[str], None] = '2d1305695e6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upgrade() -> None:
    bind = op.get_bind()

    domains_table = sa.table(
        "assessment_domains",
        sa.column("id", GUID()), sa.column("slug", sa.String()),
        sa.column("name", sa.String()), sa.column("description", sa.String()),
        sa.column("created_at", sa.DateTime()),
    )
    concepts_table = sa.table(
        "concepts",
        sa.column("id", GUID()), sa.column("domain_id", GUID()), sa.column("skill_id", GUID()),
        sa.column("slug", sa.String()), sa.column("name", sa.String()), sa.column("description", sa.String()),
    )
    deps_table = sa.table(
        "concept_dependencies", sa.column("concept_id", GUID()), sa.column("depends_on_id", GUID()),
    )
    questions_table = sa.table(
        "questions",
        sa.column("id", GUID()), sa.column("domain_id", GUID()), sa.column("concept_id", GUID()),
        sa.column("question_type", sa.String()), sa.column("prompt", sa.String()),
        sa.column("options", JSONBType()), sa.column("correct_answer", JSONBType()),
        sa.column("explanation", sa.String()), sa.column("difficulty", sa.Integer()),
        sa.column("target_role_relevance", JSONBType()), sa.column("created_at", sa.DateTime()),
    )
    resources_table = sa.table(
        "resources",
        sa.column("id", GUID()), sa.column("title", sa.String()), sa.column("provider", sa.String()),
        sa.column("url", sa.String()), sa.column("resource_type", sa.String()),
        sa.column("skill_id", GUID()), sa.column("concept_id", GUID()),
        sa.column("difficulty", sa.Integer()), sa.column("duration_minutes", sa.Integer()),
        sa.column("quality_score", sa.Numeric()), sa.column("language", sa.String()),
        sa.column("cost", sa.String()), sa.column("prerequisites", JSONBType()),
        sa.column("source_verified", sa.Boolean()), sa.column("description", sa.String()),
        sa.column("created_at", sa.DateTime()),
    )
    skills_table = sa.table("skills", sa.column("id", GUID()), sa.column("name", sa.String()))

    skill_id_by_name = {
        row.name: row.id for row in bind.execute(sa.select(skills_table.c.id, skills_table.c.name))
    }

    domain_id_by_slug = {d["slug"]: uuid.uuid4() for d in DOMAINS}
    op.bulk_insert(
        domains_table,
        [
            {
                "id": str(domain_id_by_slug[d["slug"]]), "slug": d["slug"], "name": d["name"],
                "description": d["description"], "created_at": _now(),
            }
            for d in DOMAINS
        ],
    )

    concept_id_by_key: dict[tuple[str, str], uuid.UUID] = {
        (c[0], c[1]): uuid.uuid4() for c in CONCEPTS
    }
    op.bulk_insert(
        concepts_table,
        [
            {
                "id": str(concept_id_by_key[(domain_slug, slug)]),
                "domain_id": str(domain_id_by_slug[domain_slug]),
                "skill_id": str(skill_id_by_name[skill_name]) if skill_name else None,
                "slug": slug, "name": name, "description": description,
            }
            for domain_slug, slug, name, skill_name, description in CONCEPTS
        ],
    )

    def _concept_id(domain_slug: str, concept_slug: str) -> uuid.UUID:
        return concept_id_by_key[(domain_slug, concept_slug)]

    dep_rows = []
    for concept_slug, depends_on_slug in CONCEPT_DEPENDENCIES:
        domain_slug = next(c[0] for c in CONCEPTS if c[1] == concept_slug)
        dep_rows.append(
            {
                "concept_id": str(_concept_id(domain_slug, concept_slug)),
                "depends_on_id": str(_concept_id(domain_slug, depends_on_slug)),
            }
        )
    op.bulk_insert(deps_table, dep_rows)

    op.bulk_insert(
        questions_table,
        [
            {
                "id": str(uuid.uuid4()),
                "domain_id": str(domain_id_by_slug[q["domain"]]),
                "concept_id": str(_concept_id(q["domain"], q["concept"])),
                "question_type": q["question_type"],
                "prompt": q["prompt"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"],
                "difficulty": q["difficulty"],
                "target_role_relevance": q["target_role_relevance"],
                "created_at": _now(),
            }
            for q in QUESTIONS
        ],
    )

    resource_rows = []
    for r in RESOURCES:
        resource_domain_slug = next(c[0] for c in CONCEPTS if c[1] == r["concept"])
        resource_rows.append(
            {
                "id": str(uuid.uuid4()),
                "title": r["title"], "provider": r["provider"], "url": r["url"],
                "resource_type": r["resource_type"],
                "skill_id": str(skill_id_by_name[r["skill"]]) if r.get("skill") else None,
                "concept_id": str(_concept_id(resource_domain_slug, r["concept"])),
                "difficulty": r["difficulty"], "duration_minutes": r["duration_minutes"],
                "quality_score": r["quality_score"], "language": "en", "cost": r["cost"],
                "prerequisites": [], "source_verified": True, "description": r["description"],
                "created_at": _now(),
            }
        )
    op.bulk_insert(resources_table, resource_rows)


def downgrade() -> None:
    op.execute("DELETE FROM resources")
    op.execute("DELETE FROM questions")
    op.execute("DELETE FROM concept_dependencies")
    op.execute("DELETE FROM concepts")
    op.execute("DELETE FROM assessment_domains")
