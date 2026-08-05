# Current Checkpoint

## Independent adversarial audit pass (2026-08-05, this pass)

Closes the two genuine gaps the prior "Final Beast Master" pass disclosed
honestly (below, unchanged) — demo dataset completeness and the ablation
harness — plus one real bug found and fixed along the way. Everything
below is independently re-verified in this pass, not assumed from the
prior pass's claims.

**What changed:**

1. **Demo dataset completeness** (`app/seed/seed_demo.py`): the seeded
   demo account now has a real completed Interview Arena session (4
   questions, mixed mode, one answer via a real audio fixture, real
   resume-claim evidence verification, real Interview Replay timeline
   markers, real Career Twin impact), 4 real Experiment Lab scenarios
   (SQL, Data Structures, Communication, a balanced 30h mix), and a full
   run of the Research Lab suite (all 6 ablations) — all through the same
   service layer the live screens call, not hand-crafted rows. Competition
   Mode steps 9-11 (previously honest empty states) now show real data.
   The Neo4j graph seed also now runs automatically on every container
   boot (was a manual `docker compose exec` step) — "restart the backend
   container" is now a genuine one-click demo reset with zero manual
   commands.
2. **All six ablation seams** (`app/evaluation/ablations.py`, new): seams
   1-3 (CARE, graph retrieval, vector retrieval) reuse the existing
   Experiment A/B code with explicit ablation labels; seams 4-6 (Career
   Twin memory, reflection, consensus) are a new harness that calls the
   real `MemoryAgent`/`CriticAgent`/`ConsensusAgent` over curated case
   sets and reports real before/after deltas — including one honest
   negative finding (`MemoryOutput.confidence` is currently a constant,
   not graded — disclosed, not hidden). New API endpoint `POST
   /research/experiments/ablations`, new Research Lab UI card, 12 new
   backend tests (`test_ablations.py`). See `docs/research/ABLATION_GUIDE.md`.
3. **Real bug found and fixed**: seven cross-table foreign keys (e.g.
   `interview_sessions.target_role_id`, `experiment_results.baseline_
   snapshot_id`) had no `ON DELETE` behavior. Once the demo account had
   real interview/experiment/Career-Twin history (from fix #1 above), the
   very next backend restart's reseed crashed with a Postgres
   `ForeignKeyViolation` deleting the old demo account — a real,
   reproducible bug this same pass's changes exposed, caught by actually
   restarting the container rather than assuming it would work. Fixed
   with `ON DELETE SET NULL` on all seven (migration `074b58839c25`,
   Postgres-only — SQLite test connections don't enforce FKs in this
   project so the migration is a guarded no-op there). Live-verified with
   three consecutive backend restarts against real Postgres from a fresh
   volume, each recovering in ~10 seconds (target was <15s).
4. **One real UI bug found and fixed**: the four role-gated dashboards
   (admin/faculty/placement/recruiter) rendered a generic red "Something
   went wrong" / "Try again" error card for what is actually a correct
   403 authorization boundary — alarming and misleading (retrying repeats
   the same denial forever). `components/ui/error-state.tsx` now renders
   a calm "Access restricted" state with a link back to the dashboard
   when the error is a 403, found via live adversarial browser testing of
   unauthorized access (not a code read).

**Verified live, this pass:**

- Clean `docker compose down -v && build --no-cache && up -d` from empty
  volumes: migrations run clean, graph seed runs automatically, demo seed
  runs automatically, all 5 services healthy, `/health/dependencies`
  returns `ok` with all three dependencies `true`.
- Restart persistence for a throwaway non-demo account across `docker
  compose restart backend postgres neo4j` (created via the real
  `/auth/register` API, deleted afterward via the real Responsible AI
  account-deletion endpoint).
- Neo4j outage, Redis outage, and **Postgres outage** (not previously
  tested live) — `/health` and `/health/dependencies` stayed responsive
  and honestly reported `degraded` in all three cases; full recovery
  confirmed after restarting each service.
- Cross-user IDOR, role-based 403s, rate limiting, CORS, and Responsible
  AI export/deletion isolation — see `docs/security/SECURITY_REVIEW.md`
  "Independent re-verification pass."
- Full browser walkthrough of every major route (dashboard, Career Twin,
  resume, job match, assessment, Interview Arena + Replay, Experiment
  Lab, Research Lab, Trust Center, Responsible AI, settings, all four
  role-gated dashboards, Competition Mode all 14 steps) as the demo
  student — no broken links, no raw JSON exposure, no empty major stage.
- Quality gate re-run after every change (see below) — 165 backend tests
  (up from 159), 68 frontend tests (unchanged — no new frontend test
  file was warranted for a two-branch UI fix already covered by existing
  role-dashboard tests), ruff/mypy/tsc/eslint all clean, `next build`
  succeeds (24 routes, unchanged).

**What's still honestly not done** (unchanged from the prior pass, not
newly discovered): no recorded video, printed poster, or physical stage
rehearsal (require a human and physical hardware); a dedicated axe-core
accessibility audit across all 24 routes wasn't run (manual spot-checks
only); dependency vulnerability scanning (`pip-audit`/`npm audit`)
wasn't run. See `docs/implementation/FINAL_ACCEPTANCE_MATRIX.md` for the
full item-by-item status.

## "Final Beast Master" pass (prior pass, unchanged below)

Last verified: 2026-08-05. **"Final Beast Master" pass complete.** Every
milestone independently tested and Docker-verified: **P0 (Interview
Arena)**, **Career Twin `twin-v2` safeguard**, **P1 (Experiment Lab +
Simulation Engine)**, **Responsible AI Center**, **Research Benchmark Lab**
(routing comparison + graph-vs-vector + calibration), a **security review
pass** (3 real medium-severity fixes: audio upload size/type validation,
Redis-backed auth rate limiting), **minimal role dashboards** (faculty/
placement/recruiter/admin), **Competition Mode** (live end-to-end 14-step
smoke test passed), a **premium UI pass** (1 real bug found and fixed:
toast notifications blocking the header theme-toggle button), a
**production engineering pass** (consolidated `/health/dependencies`
endpoint; confirmed request-ID middleware and structured logging were
already in place from Phase 2; live-verified degraded/recovered status
against the real Docker stack), and **final acceptance testing**
(`FINAL_ACCEPTANCE_MATRIX.md`, `FINAL_RELEASE_COMPLETION_REPORT.md`). See
`FINAL_BEAST_MASTER_EXECUTION_PLAN.md` for the full sequencing and honest
scoping statement; `PHASE_3_EXECUTION_PLAN.md` for the P0/P1 narrative;
`FINAL_ACCEPTANCE_MATRIX.md` for the item-by-item status of every area the
original release scope named. Phase 2's original validation remains below,
unchanged and still green.

## What's left, stated honestly

**(Superseded by the adversarial audit pass above.)** The two pre-demo
housekeeping steps this section used to list (run one real Interview
Arena session and one real Experiment Lab scenario before presenting) are
done automatically now — the demo seed does this on every container
boot, no manual pre-demo action required. See "Independent adversarial
audit pass" at the top of this file. Everything else in
`FINAL_ACCEPTANCE_MATRIX.md`'s "Known gaps" section is future-work, not a
defect.

## Latest quality gate (2026-08-05, after the adversarial audit pass)

```
backend:  pytest -q                         -> 165 passed
          ruff check app tests              -> clean
          mypy app --ignore-missing-imports -> clean (152 files)
          alembic heads                     -> single head 074b58839c25
frontend: tsc --noEmit / eslint             -> clean
          vitest run                        -> 68 passed (17 files)
          next build                        -> succeeds (24 routes)
```

## Prior quality gate (after the production engineering pass, superseded above)

```
backend:  pytest -q                         -> 159 passed
          ruff check app tests              -> clean
          mypy app --ignore-missing-imports -> clean (151 files)
frontend: tsc --noEmit / eslint             -> clean
          vitest run                        -> 68 passed (17 files)
          next build                        -> succeeds (24 routes)
docker:   backend rebuilt this pass; all 5 services healthy;
          live-verified GET /api/v1/health/dependencies: "ok" with all 3
          dependencies true, then stopped neo4j+redis and confirmed
          "degraded" with database still true (base /health stayed 200
          throughout), then restarted both and confirmed recovery back
          to "ok"
git:      11 commits this pass (e1f8bf5 P0+P1, efb2c28 Responsible AI,
          654ea12 Research Lab, e238b16 Security review, 7943578 role
          dashboards, 356b6bc Competition Mode, 1765743 presentation/
          research docs, 8c7aac7 toast/theme-toggle fix, 6a94ea4
          dependency-health endpoint, c73c998 production-engineering
          checkpoint, plus this pass's final acceptance-matrix/completion-
          report commit) -- all on `main`

Live e2e smoke test (this pass): logged into Docker frontend as
demo.student@careerpilot.ai, walked all 14 Competition Mode steps via
keyboard nav, confirmed evidence-backed numbers matched the dashboard,
confirmed honest empty states on steps with no stored data (not
fabricated), confirmed Escape exits cleanly to /dashboard.
```

## Exact next unfinished task

None outstanding from the Final Beast Master scope. See
`FINAL_RELEASE_COMPLETION_REPORT.md` §6 for optional future work
(pre-demo data seeding for Competition Mode steps 9-11, automated
ablation harness, dedicated accessibility audit).

## Status: Phase 3 P0 + P1 complete

### Career Experiment Lab + Simulation Engine (P1)

Deterministic, versioned (`sim-v1`) what-if simulation over hour
allocations (skill + activity type + hours, mixed allocations supported),
grounded in the student's real Career Twin, evidence diversity, concept
dependencies, their own job description's requirements, and their own
historical Career Twin trend — never an LLM-computed number.
`ExperimentExplainerAgent` may restate the numbers in prose but has no path
to alter them. New: `backend/app/simulation/engine.py`,
`backend/app/services/experiment_service.py`, `backend/app/agents/
experiment_explainer_agent.py`, `backend/app/api/experiments.py`,
`backend/app/schemas/experiment.py`, `backend/app/models/experiment.py`,
migration `957a79bda179`, frontend `/experiment-lab`. Full formula in
`docs/implementation/EXPERIMENT_LAB_SIMULATION.md`.

Verified live: ran "20h SQL", "20h DSA", and "20h Communication" scenarios
against a real student's Career Twin through the Docker stack, then
compared all three side by side (assumptions, evidence-used counts, and
the mandatory disclaimer all correct on every card).

### Quality gate for this checkpoint (cumulative)

```
backend:  pytest -q                         -> 133 passed (117 P0-checkpoint baseline + 16 new P1 tests)
          ruff check app tests              -> clean
          mypy app --ignore-missing-imports -> clean (139 files)
frontend: tsc --noEmit / eslint             -> clean
          vitest run                        -> 53 passed (50 P0-checkpoint baseline + 3 new P1 tests)
          next build                        -> succeeds (19 routes, incl. /experiment-lab)
docker:   backend + frontend images rebuilt; all 5 services healthy;
          migration head 957a79bda179
```

### Interview Arena (P0)

Full voice/typed mock-interview loop: session start (6 modes) → question →
recording-or-typed answer → CARE-routed multi-agent evaluation → Interview
Replay → Trust Center trace → Career Twin evidence. Real route diversity
(confirmed live, not just asserted): a strong, on-topic technical answer
settles on `single_agent`; a thin/off-topic/ungrounded answer is honestly
flagged `evidence_conflict=True` and escalates toward `multi_agent`/
`critic_reflection`.

New: `backend/app/models/interview.py`, `backend/app/services/
{interview_service,speech_to_text}.py`, 5 new agents (`communication_agent`,
`technical_agent`, `hr_agent`, `resume_evidence_agent`, `jd_alignment_agent`),
`backend/app/api/interviews.py`, `backend/app/schemas/interview.py`,
migration `ccca34eecf1f`, frontend `/interview`, `/interview/[sessionId]`,
`/interview/[sessionId]/replay`.

### Career Twin small-sample safeguard (`twin-v2`)

A scoring-integrity review after the first live Interview Arena walkthrough
found that a single two-question session had produced a Career Twin
snapshot reading "Technical 90%, Communication 100%" — technically paired
with low confidence (28%/37%), but not visibly guarded against, and with no
distinction between "evidence repeated from one source" and "evidence from
independent sources." Fixed with three deterministic, versioned levers in
`backend/app/career_twin/scoring.py` (formula bumped `twin-v1` →
`twin-v2`): evidence-diversity weighting, prior-weighted (Bayesian
shrinkage) scoring that pulls the *stored score itself* toward a neutral
0.5 prior when evidence is sparse/narrow (not just confidence), and a hard
confidence cap (0.50) plus explicit `is_low_sample`/`low_sample_notice`
fields below the stability thresholds (3+ evidence items, 2+ distinct
source types). Verified live: the same test account's next interview
session produced version 2 with Technical shrunk 90%→60% (confidence
14%), Communication 100%→75% (confidence 28%), both displaying "Strong
performance in this session, but more evidence is required to establish
long-term proficiency." Full rule in
`docs/implementation/CAREER_TWIN_SCORING.md` "Small-sample safeguard";
tests in `backend/tests/test_career_twin_small_sample_safeguard.py` (one
strong answer, several strong answers from one source, conflicting
evidence, repeated evidence from one source, evidence from multiple
independent sources — all 6 passing). Migration `7ba5f89c3126`.

### Quality gate for this checkpoint

```
backend:  pytest -q                         -> 117 passed (111 interview-arena baseline + 6 new safeguard tests)
          ruff check app tests              -> clean
          mypy app --ignore-missing-imports -> clean (132 files)
frontend: tsc --noEmit / eslint             -> clean
          vitest run                        -> 50 passed (48 interview-arena baseline + 2 new safeguard-label tests)
          next build                        -> succeeds (18 routes, incl. 2 new dynamic interview routes)
docker:   backend + frontend images rebuilt; all 5 services healthy;
          migration head 7ba5f89c3126; both the Interview Arena flow and
          the twin-v2 safeguard verified live in a real browser against
          this stack (not just automated tests)
```

## Status: Phase 2 fully accepted (re-verified)

All 20 Phase 2 acceptance criteria pass. Phase 1's 20 acceptance criteria
remain green (28/28 original tests still pass, unmodified).

### This validation pass specifically proved

- **All 6 CARE routes** exercised through the real persisting
  `run_care_task()` engine (not just the pure routing function) —
  `tests/test_care_engine_routes.py`, 8/8 passing.
- **GraphRAG real-Neo4j → fallback → recovery**, live: stopped Neo4j
  mid-session, confirmed no crash, confirmed the relational fallback
  returns an identical path labeled `graph_source: "relational_fallback"`,
  restarted Neo4j, confirmed it resumed using the real graph. The Trust
  Center now surfaces this label in the UI (`AgentRunOut.output_payload`
  was previously omitted from the API response).
- **The full student journey through the actual frontend browser**:
  dashboard → root cause → Trust Center → 13-question adaptive assessment
  (including a free-form AI-graded question) → Career Twin v4→v5 → change
  explanation, all clicked through by hand, not scripted against the API.
- **Restart persistence** for a real (non-demo) student's assessment
  attempt, evidence, mission, Twin history, `CareExecution`, and
  `AgentRun` rows across `docker compose restart backend postgres neo4j`
  — every ID and value matched exactly before and after. (The seeded demo
  account is unsuitable for this proof: it resets by design on every
  backend restart — see the note below.)
- **Cross-student authorization isolation**, live and now a permanent
  suite: `tests/test_authorization_isolation.py`, 7/7 passing.
- **Frontend test coverage for every new Phase 2 screen**: 16 → 40 tests.

## What's running right now

```
docker compose ps
```

| Service  | Image                    | Port(s)            | State           |
|----------|--------------------------|---------------------|-----------------|
| postgres | pgvector/pgvector:pg16   | 5432                | healthy         |
| redis    | redis:7-alpine           | 6379                | healthy         |
| neo4j    | neo4j:5-community        | 7474, 7687          | healthy — seeded (16 concepts, 14 deps, 20 questions, 14 resources, 55 skills, 2 job roles) |
| backend  | careerpilot-ai-backend   | 8000                | running         |
| frontend | careerpilot-ai-frontend  | 3000                | running         |

Started via `docker compose up --build -d`. Graph seeded via
`docker compose exec backend python -m app.graphrag.run_seed` (idempotent,
safe to re-run any time — every write is a Cypher `MERGE`).

## URLs

- Frontend: http://localhost:3000 (`/dashboard`, `/assessment`,
  `/trust-center`, `/career-twin`, `/resume`, `/job-description`,
  `/settings`)
- Backend health: http://localhost:8000/api/v1/health
- Graph health: http://localhost:8000/api/v1/graph/health
- API docs: http://localhost:8000/docs

## Demo credentials

```
Email:    demo.student@careerpilot.ai
Password: DemoPass!2026
```
Seeded student now has a real weak-SQL-JOIN evidence point, producing a live
"Close the gap: Inner Join" mission with a real GraphRAG-derived root cause
the moment the seed script runs — no manual setup needed.

## Migration state

```
docker compose exec backend alembic current
# -> 298c98dafbbb (head)
```

Four migrations total: `788d1325f003` (Phase 1 schema), `2e021960668e`
(roles/skills seed), `2d1305695e6c` (Phase 2 schema — assessment/resource/
care/retrieval/evaluation tables), `298c98dafbbb` (assessment taxonomy +
resource catalog seed).

## Bug found and fixed in this checkpoint

**Postgres-only migration failure**: `2d1305695e6c` added `NOT NULL` JSON
columns (`tasks`, `resource_ids`, `outcome_evidence_ids`) to the existing
`learning_missions` table without a `server_default`. SQLite's lenient
`ALTER TABLE` hid this in local testing (empty table every time, fresh
per-test DB); real Postgres rejected it against a table that already had
rows (`column "tasks" ... contains null values`) — caught only once this
migration ran against the persistent, non-empty Postgres volume in Docker.
Fixed with `server_default='[]'` on all three columns; re-verified with a
full container rebuild against the same non-empty database (the failed
migration rolled back transactionally, so no manual cleanup was needed).

## Second bug found and fixed: Trust Center silently omitted `graph_source`

`AgentRunOut` (the API schema for a CARE agent run) didn't include the
`output_payload` column, even though the ORM model always stored it — so
the GraphRAG agent's `graph_source` field ("neo4j" vs.
"relational_fallback") was captured in the database but never reached the
API response or the Trust Center UI. Found while proving the Neo4j
fail/recover cycle end-to-end (§18.3 of the completion report). Fixed by
adding `output_payload: dict` to `AgentRunOut` and a "Neo4j graph" /
"Relational fallback (Neo4j unavailable)" badge to `/trust-center`;
covered by `test_trust_center_labels_relational_fallback_when_neo4j_query_fails`.

## Quality gate (all green as of this checkpoint)

```
backend:  pytest -q         -> 89 passed (73 prior + 8 CARE-route + 7 auth-isolation + 1 fallback-label)
          ruff check app    -> clean
          mypy app          -> 0 errors / 122 files
frontend: tsc --noEmit      -> clean
          eslint            -> clean
          vitest run        -> 40 passed (16 prior + 24 new Phase 2 screen tests)
          next build        -> succeeds (13 static routes)
docker:   all 5 services healthy; restart-persistence and Neo4j
          fail/recover cycle verified live (see completion report §18)
```

## Files changed in this checkpoint (Phase 2, on top of the Phase 1 checkpoint)

New: `backend/app/ai/**`, `backend/app/care_engine/**`, `backend/app/agents/**`,
`backend/app/graphrag/**` (seed/repository/service/schemas, was an empty
Phase 0 scaffold), `backend/app/evaluation/**`, `backend/app/services/
{retrieval_service,assessment_service,resource_service,autonomous_loop_service,
trust_center_service}.py`, `backend/app/models/{assessment,resource,care,
retrieval,evaluation}.py`, `backend/app/api/{assessments,resources,
trust_center,graphrag}.py`, `backend/app/schemas/{assessment,resource,
trust_center}.py`, `backend/alembic/versions/{2d1305695e6c,298c98dafbbb}*.py`,
`backend/app/seed/assessment_taxonomy.py`, frontend `/assessment` and
`/trust-center` pages, `hooks/use-{assessment,trust-center}.ts`,
`components/dashboard/care-activity-card.tsx`.

Modified: `backend/app/career_twin/scoring.py` (assessment component wired
in, trend/uncertainty helper), `backend/app/services/mission_service.py`
(root-cause enrichment), `backend/app/services/{resume_service,
job_description_service}.py` (retrieval indexing hooks), `backend/app/models/
{skill,mission}.py` (new columns), `backend/pyproject.toml` (+neo4j,
+anthropic), frontend `types/api.ts`, `mission-card.tsx`, `nav-links.ts`,
`dashboard/page.tsx`.

## Files changed in the final acceptance validation pass (on top of the above)

New: `backend/tests/test_care_engine_routes.py` (8 tests, all 6 CARE
routes through the real persisting engine), `backend/tests/
test_authorization_isolation.py` (7 tests, cross-student IDOR coverage),
frontend `__tests__/{assessment-page,trust-center-page,mission-card,
twin-timeline,care-activity-card}.test.tsx` (24 tests total).

Modified: `backend/app/schemas/trust_center.py` (`AgentRunOut` gained
`output_payload`), `backend/tests/test_trust_center_api.py` (added the
Neo4j-fallback-labeling test), frontend `types/api.ts` (`AgentRunOut.
output_payload`), `app/trust-center/page.tsx` (graph-source badge).

## Next time you pick this up

- The Docker stack may still be running from this session — check
  `docker compose ps` before starting a fresh one.
- If you restart the `backend` container, `demo.student@careerpilot.ai`
  resets to its known-good seeded state (by design — see "Files changed"
  above and completion report §15). Any other account's data persists
  normally across restarts.
- See `PHASE_2_COMPLETION_REPORT.md` §19 for the Phase 3 prerequisite list.
