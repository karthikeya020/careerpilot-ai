"""expand assessment question bank v2

Adds four new assessment domains (JavaScript, DSA, OOP, Java) with their own
concepts/dependencies/questions, plus a handful of extra questions on the
already-seeded SQL/Python concepts. Purely additive: never touches a row
inserted by 298c98dafbbb_seed_assessment_taxonomy_and_resource_.

Revision ID: 190e57633512
Revises: a3f1c9e6b2d4
Create Date: 2026-08-06 02:17:40.483575

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
from app.seed.assessment_taxonomy import (  # noqa: E402
    EXTRA_QUESTIONS_EXISTING,
    NEW_CONCEPT_DEPENDENCIES,
    NEW_CONCEPTS,
    NEW_DOMAINS,
    NEW_QUESTIONS,
    NEW_SKILLS,
)

# revision identifiers, used by Alembic.
revision: str = '190e57633512'
down_revision: Union[str, Sequence[str], None] = 'a3f1c9e6b2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_DOMAIN_SLUGS = [d["slug"] for d in NEW_DOMAINS]
_NEW_SKILL_NAMES = [s["name"] for s in NEW_SKILLS]


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upgrade() -> None:
    bind = op.get_bind()

    skills_table = sa.table(
        "skills",
        sa.column("id", GUID()), sa.column("name", sa.String()), sa.column("category", sa.String()),
        sa.column("aliases", JSONBType()), sa.column("description", sa.String()), sa.column("created_at", sa.DateTime()),
    )
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

    # ---- 1. New skill(s) ----
    op.bulk_insert(
        skills_table,
        [
            {
                "id": str(uuid.uuid4()), "name": s["name"], "category": s["category"],
                "aliases": s["aliases"], "description": "", "created_at": _now(),
            }
            for s in NEW_SKILLS
        ],
    )
    skill_id_by_name = {
        row.name: row.id for row in bind.execute(sa.select(skills_table.c.id, skills_table.c.name))
    }

    # ---- 2. New domains ----
    domain_id_by_slug = {d["slug"]: uuid.uuid4() for d in NEW_DOMAINS}
    op.bulk_insert(
        domains_table,
        [
            {
                "id": str(domain_id_by_slug[d["slug"]]), "slug": d["slug"], "name": d["name"],
                "description": d["description"], "created_at": _now(),
            }
            for d in NEW_DOMAINS
        ],
    )

    # ---- 3. New concepts (linked to the new domains + existing/new skills) ----
    concept_id_by_key: dict[tuple[str, str], uuid.UUID] = {
        (c[0], c[1]): uuid.uuid4() for c in NEW_CONCEPTS
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
            for domain_slug, slug, name, skill_name, description in NEW_CONCEPTS
        ],
    )

    def _new_concept_id(domain_slug: str, concept_slug: str) -> uuid.UUID:
        return concept_id_by_key[(domain_slug, concept_slug)]

    # ---- 4. New concept dependencies (within the new domains only) ----
    dep_rows = []
    for concept_slug, depends_on_slug in NEW_CONCEPT_DEPENDENCIES:
        domain_slug = next(c[0] for c in NEW_CONCEPTS if c[1] == concept_slug)
        dep_rows.append(
            {
                "concept_id": str(_new_concept_id(domain_slug, concept_slug)),
                "depends_on_id": str(_new_concept_id(domain_slug, depends_on_slug)),
            }
        )
    op.bulk_insert(deps_table, dep_rows)

    # ---- 5. Questions for the new concepts ----
    op.bulk_insert(
        questions_table,
        [
            {
                "id": str(uuid.uuid4()),
                "domain_id": str(domain_id_by_slug[q["domain"]]),
                "concept_id": str(_new_concept_id(q["domain"], q["concept"])),
                "question_type": q["question_type"],
                "prompt": q["prompt"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"],
                "difficulty": q["difficulty"],
                "target_role_relevance": q["target_role_relevance"],
                "created_at": _now(),
            }
            for q in NEW_QUESTIONS
        ],
    )

    # ---- 6. Extra questions on the ORIGINAL sql/python concepts -- look up
    # their existing domain_id/concept_id from the DB (they were created by
    # 298c98dafbbb, not by this migration). ----
    existing_domains_table = sa.table(
        "assessment_domains", sa.column("id", GUID()), sa.column("slug", sa.String())
    )
    existing_concepts_table = sa.table(
        "concepts", sa.column("id", GUID()), sa.column("domain_id", GUID()), sa.column("slug", sa.String())
    )
    existing_domain_id_by_slug = {
        row.slug: row.id for row in bind.execute(sa.select(existing_domains_table.c.id, existing_domains_table.c.slug))
    }
    existing_concept_rows = bind.execute(
        sa.select(existing_concepts_table.c.id, existing_concepts_table.c.domain_id, existing_concepts_table.c.slug)
    ).all()
    existing_concept_id_by_key: dict[tuple[str, str], object] = {}
    domain_slug_by_id = {v: k for k, v in existing_domain_id_by_slug.items()}
    for row in existing_concept_rows:
        domain_slug = domain_slug_by_id.get(row.domain_id)
        if domain_slug:
            existing_concept_id_by_key[(domain_slug, row.slug)] = row.id

    op.bulk_insert(
        questions_table,
        [
            {
                "id": str(uuid.uuid4()),
                "domain_id": str(existing_domain_id_by_slug[q["domain"]]),
                "concept_id": str(existing_concept_id_by_key[(q["domain"], q["concept"])]),
                "question_type": q["question_type"],
                "prompt": q["prompt"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"],
                "difficulty": q["difficulty"],
                "target_role_relevance": q["target_role_relevance"],
                "created_at": _now(),
            }
            for q in EXTRA_QUESTIONS_EXISTING
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    domains_table = sa.table("assessment_domains", sa.column("id", GUID()), sa.column("slug", sa.String()))
    new_domain_ids = [
        row.id for row in bind.execute(
            sa.select(domains_table.c.id).where(domains_table.c.slug.in_(_NEW_DOMAIN_SLUGS))
        )
    ]
    extra_question_prompts = [q["prompt"] for q in EXTRA_QUESTIONS_EXISTING]

    questions_table = sa.table("questions", sa.column("domain_id", GUID()), sa.column("prompt", sa.String()))
    op.execute(questions_table.delete().where(questions_table.c.domain_id.in_(new_domain_ids)))
    if extra_question_prompts:
        op.execute(questions_table.delete().where(questions_table.c.prompt.in_(extra_question_prompts)))

    concepts_table = sa.table("concepts", sa.column("id", GUID()), sa.column("domain_id", GUID()))
    new_concept_ids = [
        row.id for row in bind.execute(
            sa.select(concepts_table.c.id).where(concepts_table.c.domain_id.in_(new_domain_ids))
        )
    ]
    deps_table = sa.table("concept_dependencies", sa.column("concept_id", GUID()))
    if new_concept_ids:
        op.execute(deps_table.delete().where(deps_table.c.concept_id.in_(new_concept_ids)))
    op.execute(concepts_table.delete().where(concepts_table.c.domain_id.in_(new_domain_ids)))
    op.execute(domains_table.delete().where(domains_table.c.slug.in_(_NEW_DOMAIN_SLUGS)))

    skills_table = sa.table("skills", sa.column("name", sa.String()))
    op.execute(skills_table.delete().where(skills_table.c.name.in_(_NEW_SKILL_NAMES)))
