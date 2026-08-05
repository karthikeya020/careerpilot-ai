# Final Truth-First Defect Ledger

Started 2026-08-06. This ledger records defects reproduced against the
**actual running product** (Docker stack, real Postgres/Neo4j, live
browser), not against completion-report claims. Every entry states its
real current status — PASS only when repaired and live-verified, PARTIAL
when partially true, BLOCKED/DEFERRED when genuinely not attempted this
pass, with the reason stated. Nothing here is marked done that isn't.

This ledger will grow across sessions. See `CURRENT_CHECKPOINT.md` for
which defect was being worked when a session ended, and
`FINAL_TRUTH_FIRST_RESCUE_PLAN.md` for the prioritization rationale behind
what got attempted first.

---

## DEFECT-001 — Resume replacement does not invalidate the prior resume's evidence

**Severity**: Critical. **Status**: **PASS** — repaired and live-verified this pass.

**User impact**: A student who uploads a second, different resume (e.g.
switching from a backend-focused resume to a data-focused one) continued
to have skills from the *first* resume count toward their Career Twin
score and job/JD match coverage forever, with no way to see this was
happening or to fix it. This directly undermines Constitution rule 13
("no stale analysis after a resume changes") and rule 1 (every score must
be derived from *current* evidence) — the single most severe defect
found this pass, and the reason it was fixed first.

**Reproduction steps** (as originally described and as verified):
1. Upload a resume containing Java/Spring/SQL skills.
2. Upload a second, unrelated resume containing Python/Pandas/NumPy
   skills, with no overlap.
3. Check the Career Twin, job-description match coverage, or resume
   skill list — skills from the *first* resume are still present and
   still counted.

**Expected behavior**: Uploading a new resume makes it the *active*
resume. Skills sourced only from a prior resume must stop counting toward
the Career Twin, JD/job matching, and any other "current profile" view.
The prior resume must remain visible in history (never deleted), and the
student must be able to see which resume is active and reactivate an
older one if they choose.

**Actual behavior (before fix)**: `Resume` had no active/version concept
at all. `resume_service.process_resume` wrote permanent `SkillEvidence`
rows tagged `source_object_type="resume", source_object_id=<resume.id>`
on every upload, and every consumer (`career_twin/scoring.py`'s
`_compute_components`, `job_description_service.py`'s
`_resume_weight_by_skill`) queried **all** `SkillEvidence` for the
student with no resume-recency or activeness filter. Evidence from every
resume ever uploaded accumulated forever.

**Root cause**: No `Resume.is_active` concept existed; every
`SkillEvidence` consumer queried by `student_profile_id` alone.

**Files involved**:
- `backend/app/models/resume.py` — added `is_active`, `superseded_at`.
- `backend/alembic/versions/a3f1c9e6b2d4_resume_active_version_tracking.py` — migration + real backfill.
- `backend/app/services/evidence_service.py` — **new**, the shared active-evidence query.
- `backend/app/services/resume_service.py` — supersession on upload, `list_resumes`, `activate_resume`.
- `backend/app/career_twin/scoring.py` — now uses `get_active_skill_evidence`.
- `backend/app/services/job_description_service.py` — now uses `get_active_skill_evidence`.
- `backend/app/api/resumes.py` — new `GET /resumes` (history), `POST /resumes/{id}/activate`.
- `backend/app/schemas/resume.py` — `ResumeOut`/`ResumeSummaryOut` gained `is_active`/`superseded_at`.
- `frontend/app/resume/page.tsx`, `frontend/hooks/use-resume.ts`, `frontend/types/api.ts` — active badge, resume-history card, reactivate action.

**Repair**: Exactly one resume per student is active at a time.
`process_resume` marks a newly-parsed resume active and supersedes all
others (audit-logged). `career_twin/scoring.py` and
`job_description_service.py` now read evidence through
`evidence_service.get_active_skill_evidence`, which excludes
resume-sourced `SkillEvidence` whose owning resume is superseded, while
leaving non-resume evidence (assessment, interview, project) and
evidence with no resolvable resume row (defensive default, matches
pre-existing unit-test fixtures) untouched. Career Twin recomputes
immediately on both upload and explicit reactivation. Job/JD matching
needed no separate recompute trigger — `compute_match` was already a
live, uncached computation, so the fix takes effect on the very next
`GET .../match` call.

**Automated test**:
`backend/tests/test_resumes.py::test_replacing_a_resume_supersedes_the_old_one_and_removes_its_evidence_from_the_active_profile`
— uploads a Java-heavy resume, posts a JD requiring Java+Pandas, confirms
Java matches; uploads an unrelated Python/Pandas resume, confirms it
becomes active, confirms the *old* resume is preserved in history as
superseded (not deleted), confirms the JD match no longer counts Java and
now counts Pandas; reactivates the old resume, confirms Java counts
again. Plus
`test_resume_history_and_activation_are_isolated_per_student` (a second
student cannot see or activate another student's resume — 404, not 403,
matching existing cross-tenant-isolation convention in this codebase).
Both pass. Full backend suite: **167/167 passed** (was 165; the 3
tests that initially regressed from the evidence-filter change —
`test_conflicting_evidence_lowers_confidence_and_is_flagged`,
`test_evidence_from_multiple_independent_sources_clears_low_sample`,
`test_positive_historical_trend_boosts_projected_gain` — were a real bug
in the first version of the filter (it excluded resume-tagged evidence
with no matching `Resume` row, which is exactly what those unit tests'
fixtures create) and were fixed by adding the "no matching resume row →
treat as active" branch to `evidence_service.active_skill_evidence_statement`,
not by weakening the tests.

**Browser verification** (live, against the real Docker stack, demo
account `demo.student@careerpilot.ai`): uploaded a real
`resume-b-python-data.docx` (Python/Pandas/NumPy/Git) over the seeded
`aanya_sharma_resume.docx` (PostgreSQL/REST APIs/Python/Docker/SQL/Git/
FastAPI/Data Structures/AWS). Confirmed:
- `/resume`: new resume shows "Active resume" badge; old resume appears
  in a new "Resume history" card marked "Superseded [timestamp]" with a
  "Make active" button; "Detected skills" list changed from 9 items to
  the 4 new ones.
- `/job-description`: the seeded "Backend Engineering Intern @
  NimbusTech" JD's coverage **dropped from 67% to 11%** live, with SQL,
  PostgreSQL, FastAPI, Docker, REST APIs moving from "Matched" to
  "Missing" — proving the match is a live recomputation, not a stale
  cached value.
- Clicked "Make active" on the old resume: toast confirmed "Career Twin,
  job matches, and missions have been recomputed"; the badge flipped
  back; coverage on the same JD **returned to 67%** with the original
  skills matched again.
- Zero console errors throughout (`read_console_messages`, empty).

**Screenshot evidence**: not saved to disk as image files this pass
(verified via live screenshot inspection during the session, not
archived) — see "Remaining limitations" in the rescue plan.

**Real, unplanned corroborating evidence**: the migration's backfill
step, run against the actual non-test Postgres volume (which already had
manual test data from earlier manual testing, unrelated to this
session), found a real student with **two pre-existing resume rows both
implicitly "active"** under the new column's default, and correctly
resolved it to a single active resume (the more recently uploaded one),
marking the other superseded with a real timestamp — confirmed via
`docker compose exec postgres psql`. This is stronger evidence the
backfill logic is correct than a staged scenario would have been, since
it wasn't constructed by this session.

**Final state**: PASS. Migrated cleanly against non-empty real Postgres
(`alembic heads` → single head `a3f1c9e6b2d4`), backend 167/167 tests
green, ruff/mypy clean, frontend 70/70 tests green (2 new), tsc/eslint
clean, `next build` succeeds (25 routes), Docker frontend + backend
rebuilt and live-verified end to end including the reactivate-reverts
case.

**Known residual gap, stated honestly**: `app/agents/memory_agent.py`'s
"recent evidence types" recall (used only as low-stakes CARE routing
context, not a displayed score) still queries `SkillEvidence` without
the active-resume filter. It could theoretically mention a stale
resume-sourced evidence type in its internal reasoning summary. This
does not affect any displayed score, recommendation, or Career Twin
value — those all go through the fixed paths — so it was consciously
deprioritized rather than risking a same-session change to CARE routing
logic for a purely internal, non-user-facing signal. Tracked here, not
silently dropped.

---

## DEFECT-002 through DEFECT-0NN — remaining reported problem areas

The mega-prompt's Phase 0 lists roughly a dozen additional problem
categories (GraphRAG's depth, assessment-domain breadth, interview NLP
depth, job-listing deduplication, Experiment Lab clarity, Research Lab
audience-splitting, Trust Center actionability, Responsible AI
actionability, and ~15 named UI/presentation issues from a demo
recording). Investigating each against the *current* code (not
assumption) before claiming a fix, per rule 5, produced the following
honest findings. None of these were repaired this pass beyond what is
noted — see `FINAL_TRUTH_FIRST_RESCUE_PLAN.md` for why, and for the
priority order for a follow-up pass.

### GraphRAG "redirects to / duplicates the assessment page"

**Finding**: Not reproducible against the current code. `/graphrag` is a
real, dedicated Next.js route (`frontend/app/graphrag/page.tsx`, built in
the prior session) backed by the real Neo4j-backed
`GET /graph/root-cause/{question_id}` endpoint
(`backend/app/api/graphrag.py` → `app/graphrag/service.py`). It renders a
sequential node-chain reveal distinct from `/assessment` in both content
and visual design, and was live-verified working against real seeded
Neo4j data in the prior session (see `CURRENT_CHECKPOINT.md` "Premium
visual transformation pass"). **Status: PASS (pre-existing from the
immediately prior session, re-confirmed, not re-verified live again this
specific pass).** The reported symptom likely predates that session's
work, or describes a build that was live before this repository's most
recent commits.

**Architectural note found while reproducing**: the mega-prompt's Phase 1
proof list asks for "GraphRAG paths change when the active resume
changes." This is not how the feature is designed, and forcing it to be
true would be dishonest engineering: `analyze_root_cause` keys its causal
chain off a specific *missed assessment question* (`question_tests_concept`
→ `concept_dependency_chain` → `job_roles_requiring_concept` →
`resources_teaching_concept`), not off resume-derived skill evidence at
all. A root-cause chain answers "why did I get *this question* wrong,"
which is legitimately independent of what resume is currently active.
Documented here as **N/A by design**, not silently assumed or forced.

### Assessment: "only SQL and Python are visibly supported"

**Finding**: Confirmed true, and severe. `backend/app/seed/assessment_taxonomy.py`
seeds exactly 2 domains (`sql`, `python`), 15 concepts, and a small
question bank. The mega-prompt's Phase 4 asks for ~19 domains (DSA, OOP,
DBMS, OS, Networks, Java, C, C++, aptitude, quantitative/logical/verbal
reasoning, system design, software-engineering fundamentals, behavioral
prep, role-specific topics), each with a real curriculum (topic →
subtopic → concept → prerequisite graph), multiple question types,
misconception tagging, no-repeat/spaced-review tracking, and adaptive
difficulty. **Status: DEFERRED.** This is genuine content-authoring plus
engineering work on the order of weeks for real quality (each new domain
needs a real, correct, pedagogically sound question bank with
misconceptions and prerequisites — not placeholder text), not something
that can be honestly fabricated in one session without violating the
prompt's own rule 7 ("do not add preset analysis presented as
personalized") and rule 10 ("do not hardcode flattering research
results" — the parallel here is not padding a shallow feature to look
complete). Not attempted this pass beyond this honest assessment.

### Interview: "looks like a basic form" / "voice delivery not analyzed meaningfully"

**Finding**: Partially outdated. The prior session's visual pass already
rebuilt `/interview/[sessionId]` with a real Web Audio API amplitude
visualizer, live recording timer, mode-specific accent colors, and a
CARE-processing state — no longer "a basic form" visually. On the
*analysis depth* side (Phase 5's ask: pause duration, hesitation
frequency, repeated-phrase detection, speaking-rate-derived delivery
confidence with explicit "not an emotion diagnosis" framing), the
backend's `CommunicationMetricsOut` already computes word count, filler
ratio, sentence completeness, speaking rate, STAR-component detection,
clarity/conciseness/professionalism scores — real, not fabricated,
metrics — but does not yet compute pause-duration or hesitation-specific
signals, and the "ethical confidence coaching" framing Phase 5 asks for
(explicit "observable delivery signals, not an emotion diagnosis"
disclaimer) is not yet present anywhere in the product. **Status:
PARTIAL** — visual redesign PASS (prior session), deeper NLP signal
extraction and the explicit non-diagnosis framing DEFERRED this pass.

### Job matching: "the same job appears multiple times with slightly changed presentation" / provider architecture / deduplication

**Finding**: **Not applicable to the current product as built.** There is
no job-listing/marketplace/search feature in this codebase at all —
grepped for `JobPosting`, `JobListing`, `job_provider`, and no such model,
service, or route exists. The only job-related feature is `/job-description`
("Job Match"): a student pastes or selects *one* job description and gets
a single coverage analysis against their active resume — there is no list
of multiple job postings that could duplicate. Phase 6's entire premise
(provider adapters, canonical-ID deduplication, a job marketplace) assumes
a feature this product does not have. Documented honestly rather than
building a fake "fix" for a bug that cannot be reproduced because the
underlying feature doesn't exist. If a job-listing/marketplace feature is
genuinely wanted, that is new-feature work, not a bug fix, and should be
scoped as such — not silently smuggled in as though it "restores" broken
behavior.

### Experiment Lab / Research Lab / Trust Center / Responsible AI

**Finding**: The prior session's visual pass already gave Experiment Lab
a guided current→simulated reveal with confidence range and assumptions/
evidence drawers, gave Research Lab a general-audience/technical-judge
toggle, and gave Trust Center a real CARE execution timeline. These
address the *visual clarity* complaints in Phase 0 but not the *deeper
action* asks in Phases 9-10 (Trust Center: correct/exclude/recompute
evidence actions; Responsible AI: challenge-a-recommendation,
human-review-request controls beyond the existing
export/delete-audio/delete-account). **Status: PARTIAL** on all four —
visual/audience-clarity PASS (prior session), the specific new
interactive actions Phases 9-10 ask for DEFERRED this pass.

### The ~15 named UI/presentation issues from the demo recording

**Finding**: Cross-referenced against the prior session's checkpoint
(`docs/implementation/CURRENT_CHECKPOINT.md` "Premium visual
transformation pass" and the original visual-transformation pass before
it). Several are already addressed there (cinematic opening, dark theme,
sidebar hidden in Competition Mode, Career Twin's radial visual, GraphRAG
reveal, Interview Arena redesign). Several are **not** re-verified this
pass and may still be real: the reported Windows file-picker appearing
mid-demo (resume upload has no "preloaded fictional resume, one-click"
presentation-safe path — a real gap, Phase 13's ask), the reported
non-16:9 recording frame and floating-widget distraction (both relate to
recording/presentation setup, not app code), and the reported "ends on
Settings" (Competition Mode's actual closing slide was rebuilt in the
prior session to the "Past → Present → Future" framing described in
Phase 12 — this specific complaint appears to predate that fix, but
was not re-verified with a fresh full 14-step walkthrough this pass).
**Status: PARTIAL**, itemized truthfully rather than bulk-claimed.
