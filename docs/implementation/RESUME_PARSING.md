# Resume Parsing Pipeline (Phase 1, deterministic)

Implemented in `backend/app/services/resume_parser.py` (text extraction +
section detection) and `backend/app/services/resume_service.py`
(orchestration + evidence creation).

## Pipeline

1. **Validate** — extension in `.pdf`/`.docx`/`.txt`, non-empty, under
   `MAX_UPLOAD_BYTES` (default 5MB).
2. **Store** — saved to `var/uploads/<student_profile_id>/<uuid>.<ext>` via
   `app/services/storage.py` (swappable for S3/GCS later; callers never touch
   the filesystem directly).
3. **Extract text** — `pypdf` for PDF, `python-docx` for DOCX, UTF-8 decode
   for plain text.
4. **Detect sections** — line-by-line heuristic: a short line (<45 chars)
   whose letters-only lowercase form exactly matches a known heading variant
   (e.g. "technical skills", "work experience") starts a new section; content
   before the first heading or with no headings at all falls back to `other`.
   Recognized types: `summary`, `education`, `experience`, `projects`,
   `skills`, `certifications`, `achievements`, `other`.
5. **Extract skills** — each section's text is scanned against the seeded
   `Skill` taxonomy (canonical name + aliases, longest-term-first, word-
   boundary regex) via `app/services/skill_matching.find_skills_in_text`.
6. **Score evidence strength by section** — a skill mentioned in `skills` is
   the strongest signal (weight/normalized_score `1.0`); `experience`/
   `projects` are demonstrated-usage signals (`0.85`); everything else is
   incidental (`0.5`/`0.6`). If a skill appears in multiple sections, the
   strongest section wins (no double-counting). All resume-derived evidence
   uses a fixed keyword-match confidence of `0.7` — deterministic string
   matching without semantic verification, not full certainty.
7. **Persist** — one `ResumeSection` per detected section, one `ResumeSkill`
   + one `SkillEvidence` per matched skill (`evidence_type=project` when the
   winning section is Projects, `resume` otherwise), then the resume's
   `parsing_status` flips to `parsed` (or `failed` with `parsing_error` set,
   on a caught extraction error — never a silent drop).
8. **Recompute the Career Twin** — `recompute_twin(..., reason="Resume '<name>' parsed successfully.")`
   runs in the same request so `resume_readiness`, `technical_readiness`,
   `communication_readiness`, and `portfolio_readiness` pick up the new
   evidence immediately.

## Adapter boundary

`resume_parser.extract_text` / `detect_sections` are pure functions with no
knowledge of the DB or FastAPI. A future LLM-backed parser can implement the
same two function signatures and be swapped in `resume_service.py` alone.
