"""Deterministic resume-quality analysis: bullet-level evidence-strength
grading, a self-consistency check (skills claimed vs. skills evidenced), and
a parseability/ATS heuristic. All three are pure text analysis over data
already stored on the Resume/ResumeSection/ResumeSkill rows -- no model call,
no new tables, computed fresh on every read so it can never drift from the
resume actually on file (Constitution rule 1: no invented numbers).
"""

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.resume import (
    SECTION_EDUCATION,
    SECTION_EXPERIENCE,
    SECTION_PROJECTS,
    SECTION_SKILLS,
    Resume,
)
from app.services.skill_matching import find_skills_in_text

# ---------------------------------------------------------------------------
# Bullet-level evidence-strength grading
# ---------------------------------------------------------------------------

BULLET_SECTIONS = (SECTION_EXPERIENCE, SECTION_PROJECTS)

_BULLET_MARKER_RE = re.compile(r"^\s*[-*•▪‣◦●○➤→]\s+|^\s*\d+[.)]\s+")

_STRONG_VERBS = {
    "built", "designed", "led", "architected", "implemented", "optimized", "reduced", "increased",
    "launched", "automated", "developed", "engineered", "deployed", "migrated", "scaled",
    "spearheaded", "delivered", "created", "improved", "achieved", "drove", "orchestrated",
    "shipped", "refactored", "authored", "established", "accelerated", "streamlined", "resolved",
    "mentored", "negotiated", "cut", "boosted", "eliminated", "generated", "integrated", "pioneered",
    "redesigned", "trained", "coordinated", "analyzed", "debugged", "optimised", "modernized",
}

_VAGUE_STARTERS = (
    "worked on", "responsible for", "helped with", "involved in", "duties included",
    "participated in", "assisted with", "was part of", "part of a team", "tasked with",
    "in charge of", "worked with",
)

_OUTCOME_PHRASES = (
    "resulting in", "which led to", "leading to", "enabling", "reducing", "increasing", "saving",
    "improving", "achieving", "cutting", "boosting", "driving", "resulted in",
)

_METRIC_RE = re.compile(
    r"(\d+(\.\d+)?\s*%)|(\$\s?\d)|(\d+(\.\d+)?\s*(x|k|m|ms|hrs?|hours?|days?|weeks?|users?|requests?))"
    r"|(\b\d{2,}\b)",
    re.IGNORECASE,
)

BULLET_STRONG = "strong"
BULLET_MODERATE = "moderate"
BULLET_WEAK = "weak"


@dataclass
class BulletGrade:
    section_type: str
    text: str
    strength: str
    has_action_verb: bool
    has_metric: bool
    has_outcome_language: bool
    fix_suggestion: str | None


def _split_bullets(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    marked = [ln for ln in lines if ln and _BULLET_MARKER_RE.match(ln)]
    if marked:
        return [_BULLET_MARKER_RE.sub("", ln).strip() for ln in marked]
    # No bullet markers used at all -- fall back to substantial lines, since
    # some resumes format bullets as plain wrapped paragraph lines.
    return [ln for ln in lines if len(ln) >= 25]


def _grade_bullet(section_type: str, bullet: str) -> BulletGrade:
    lower = bullet.lower()
    first_words = " ".join(lower.split()[:4])

    vague_hit = next((p for p in _VAGUE_STARTERS if lower.startswith(p)), None)
    first_word = lower.split()[0].strip(".,;:") if lower.split() else ""
    has_action_verb = vague_hit is None and first_word in _STRONG_VERBS

    has_metric = bool(_METRIC_RE.search(bullet))
    has_outcome_language = has_metric or any(p in lower for p in _OUTCOME_PHRASES)

    if vague_hit:
        strength = BULLET_WEAK
        fix = (
            f"Replace vague phrasing (\"{vague_hit}\") with a strong action verb and what you "
            "specifically built or changed."
        )
    elif has_action_verb and has_outcome_language:
        strength = BULLET_STRONG
        fix = None
    elif has_action_verb or has_outcome_language:
        strength = BULLET_MODERATE
        fix = (
            "Add a measurable outcome -- how much, how many, or by what percentage did this matter?"
            if has_action_verb
            else "Start with a strong action verb (e.g. \"Built\", \"Led\", \"Optimized\") instead of a passive description."
        )
    else:
        strength = BULLET_WEAK
        fix = (
            "This reads as a vague claim, not evidence. Start with a strong action verb and add a "
            "measurable outcome (how much, how many, by what percentage)."
        )

    return BulletGrade(
        section_type=section_type,
        text=bullet,
        strength=strength,
        has_action_verb=has_action_verb,
        has_metric=has_metric,
        has_outcome_language=has_outcome_language,
        fix_suggestion=fix,
    )


def grade_bullets(resume: Resume) -> list[BulletGrade]:
    grades: list[BulletGrade] = []
    for section in resume.sections:
        if section.section_type not in BULLET_SECTIONS:
            continue
        for bullet in _split_bullets(section.raw_text):
            grades.append(_grade_bullet(section.section_type, bullet))
    return grades


# ---------------------------------------------------------------------------
# Self-consistency check: Skills-section claims vs. evidence elsewhere
# ---------------------------------------------------------------------------


@dataclass
class SelfConsistencyFlag:
    skill_id: str
    skill_name: str
    message: str


def check_self_consistency(db: Session, resume: Resume) -> list[SelfConsistencyFlag]:
    """Flags skills claimed in the resume's Skills section that have zero
    supporting mention anywhere else in the same resume -- the single most
    common resume mistake (keyword-stuffing a skills line). Re-derives which
    sections evidence each skill by re-scanning every section's raw text,
    rather than trusting resume_service's "best section wins" summary, since
    that path only keeps one winning section per skill and can't answer
    "does it ALSO appear elsewhere."
    """
    sections_by_skill: dict[str, set[str]] = {}
    for section in resume.sections:
        for skill, _term in find_skills_in_text(db, section.raw_text):
            sections_by_skill.setdefault(str(skill.id), set()).add(section.section_type)

    flags: list[SelfConsistencyFlag] = []
    for resume_skill in resume.resume_skills:
        skill_id = str(resume_skill.skill_id)
        sections = sections_by_skill.get(skill_id, set())
        if sections == {SECTION_SKILLS}:
            flags.append(
                SelfConsistencyFlag(
                    skill_id=skill_id,
                    skill_name=resume_skill.skill.name,
                    message=(
                        f"\"{resume_skill.skill.name}\" is listed in your Skills section but isn't backed up "
                        "anywhere in your Experience or Projects bullets. Recruiters (and ATS keyword checks) "
                        "read unbacked skills lines as keyword-stuffing."
                    ),
                )
            )
    return flags


# ---------------------------------------------------------------------------
# Parseability / real-ATS-check score
# ---------------------------------------------------------------------------

_EXPECTED_SECTIONS = (SECTION_SKILLS, SECTION_EDUCATION, SECTION_EXPERIENCE, SECTION_PROJECTS)
_MIN_CLEAN_TEXT_LENGTH = 200
_SHORT_TOKEN_WARNING_RATIO = 0.15


@dataclass
class ParseabilityResult:
    score: float
    warnings: list[str] = field(default_factory=list)


def score_parseability(resume: Resume) -> ParseabilityResult:
    warnings: list[str] = []
    score = 1.0
    text = resume.raw_text or ""
    stripped = text.strip()

    if len(stripped) < _MIN_CLEAN_TEXT_LENGTH:
        warnings.append(
            "Very little text could be extracted from this file. This usually means the resume is "
            "scanned as an image or built from text-in-graphics -- an automated ATS filter would see "
            "the same near-empty result and likely reject it before a human ever looks."
        )
        score -= 0.4

    present_sections = {s.section_type for s in resume.sections}
    detected_expected = [s for s in _EXPECTED_SECTIONS if s in present_sections]
    if len(detected_expected) <= 1:
        warnings.append(
            "Standard section headings (Skills, Experience, Projects, Education) weren't detected. "
            "Multi-column layouts, text boxes, or unconventional headings often cause this -- and an "
            "automated resume filter would fail to categorize your experience the same way."
        )
        score -= 0.3

    tokens = stripped.split()
    if tokens:
        short_tokens = sum(1 for t in tokens if len(re.sub(r"[^a-zA-Z0-9]", "", t)) == 1)
        short_ratio = short_tokens / len(tokens)
        if short_ratio > _SHORT_TOKEN_WARNING_RATIO:
            warnings.append(
                "The extracted text is fragmented into many single-character pieces -- a common sign of "
                "a multi-column or table-based layout that confuses automated parsers into scrambling "
                "word order."
            )
            score -= 0.2

    blank_run = 0
    max_blank_run = 0
    for line in text.splitlines():
        if not line.strip():
            blank_run += 1
            max_blank_run = max(max_blank_run, blank_run)
        else:
            blank_run = 0
    if max_blank_run > 8:
        warnings.append(
            "Long stretches of blank lines were extracted, which often means content is trapped in "
            "tables, text boxes, or columns that a linear text parser (and most ATS software) can't read "
            "in the right order."
        )
        score -= 0.1

    return ParseabilityResult(score=round(max(score, 0.1), 4), warnings=warnings)
