"""Deterministic job-description requirement extraction.

Adapter boundary, same rationale as `resume_parser.py`: line-by-line keyword
heuristics for Phase 1, swappable for an LLM-backed extractor later without
touching `job_description_service.py`.
"""

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.job_description import (
    REQUIREMENT_EDUCATION,
    REQUIREMENT_EXPERIENCE,
    REQUIREMENT_RESPONSIBILITY,
    REQUIREMENT_SKILL,
)
from app.models.skill import Skill
from app.services.skill_matching import find_skills_in_text

_EDUCATION_PATTERN = re.compile(
    r"\b(bachelor|master|b\.?tech|m\.?tech|b\.?sc|m\.?sc|degree|university|college diploma)\b", re.IGNORECASE
)
_EXPERIENCE_PATTERN = re.compile(r"\b\d+\+?\s*(years?|yrs?)\b", re.IGNORECASE)
_OPTIONAL_PATTERN = re.compile(r"\b(nice to have|preferred|bonus|plus|good to have|optional)\b", re.IGNORECASE)
_RESPONSIBILITY_HEADING = re.compile(
    r"^(responsibilit|what you.?ll do|duties|role overview|about the role)", re.IGNORECASE
)
_BULLET_PREFIX = re.compile(r"^[\s\-\*••·]+")


@dataclass
class DetectedRequirement:
    requirement_type: str
    raw_text: str
    is_required: bool
    skill: Skill | None = None


def extract_requirements(db: Session, raw_text: str) -> list[DetectedRequirement]:
    requirements: list[DetectedRequirement] = []
    seen_skill_ids: set = set()
    in_responsibilities_block = False

    for raw_line in raw_text.splitlines():
        line = _BULLET_PREFIX.sub("", raw_line).strip()
        if not line:
            continue

        if _RESPONSIBILITY_HEADING.match(line):
            in_responsibilities_block = True
            continue
        if line.isupper() and len(line) < 40 and not _RESPONSIBILITY_HEADING.match(line):
            # Any other short all-caps heading ends the responsibilities block.
            in_responsibilities_block = False

        is_required = not _OPTIONAL_PATTERN.search(line)

        if _EDUCATION_PATTERN.search(line):
            requirements.append(DetectedRequirement(REQUIREMENT_EDUCATION, line, is_required))
            continue
        if _EXPERIENCE_PATTERN.search(line):
            requirements.append(DetectedRequirement(REQUIREMENT_EXPERIENCE, line, is_required))
            continue

        skill_matches = find_skills_in_text(db, line)
        if skill_matches:
            for skill, _term in skill_matches:
                if skill.id in seen_skill_ids:
                    continue
                seen_skill_ids.add(skill.id)
                requirements.append(DetectedRequirement(REQUIREMENT_SKILL, line, is_required, skill=skill))
            continue

        if in_responsibilities_block and len(line) > 15:
            requirements.append(DetectedRequirement(REQUIREMENT_RESPONSIBILITY, line, is_required))

    return requirements
