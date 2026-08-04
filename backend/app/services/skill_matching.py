"""Shared deterministic skill-name resolution against the seeded Skill taxonomy.

Used by onboarding (self-assessed skills), the resume parser, and the job
description extractor so all three speak the same skill vocabulary.
"""

import re

from sqlalchemy.orm import Session

from app.models.skill import Skill

_WORD_BOUNDARY_CACHE: dict[str, re.Pattern] = {}


def _all_skills(db: Session) -> list[Skill]:
    return list(db.query(Skill).all())


def find_skill_by_name(db: Session, name: str) -> Skill | None:
    """Case-insensitive exact match against a skill's canonical name or aliases."""
    needle = name.strip().lower()
    if not needle:
        return None
    for skill in _all_skills(db):
        if skill.name.lower() == needle:
            return skill
        if needle in (alias.lower() for alias in skill.aliases):
            return skill
    return None


def _pattern_for(term: str) -> re.Pattern:
    if term not in _WORD_BOUNDARY_CACHE:
        escaped = re.escape(term.lower())
        _WORD_BOUNDARY_CACHE[term] = re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")
    return _WORD_BOUNDARY_CACHE[term]


def find_skills_in_text(db: Session, text: str) -> list[tuple[Skill, str]]:
    """Scan free text for skill/alias mentions. Returns (skill, matched_term) pairs,
    longest terms matched first so e.g. "Node.js" wins over a bare "Node" collision."""
    haystack = text.lower()
    matches: list[tuple[Skill, str]] = []
    seen_skill_ids = set()

    all_terms: list[tuple[str, Skill]] = []
    for skill in _all_skills(db):
        all_terms.append((skill.name, skill))
        for alias in skill.aliases:
            all_terms.append((alias, skill))
    all_terms.sort(key=lambda pair: len(pair[0]), reverse=True)

    for term, skill in all_terms:
        if skill.id in seen_skill_ids:
            continue
        if _pattern_for(term).search(haystack):
            matches.append((skill, term))
            seen_skill_ids.add(skill.id)
    return matches
