# Current Checkpoint

Last verified: 2026-08-05, "Final Beast Master" pass in progress. Complete
so far, each independently tested and Docker-verified: **P0 (Interview
Arena)**, **Career Twin `twin-v2` safeguard**, **P1 (Experiment Lab +
Simulation Engine)**, **Responsible AI Center**, **Research Benchmark Lab**
(routing comparison + graph-vs-vector + calibration), and a **security
review pass** (3 real medium-severity fixes: audio upload size/type
validation, Redis-backed auth rate limiting). See
`FINAL_BEAST_MASTER_EXECUTION_PLAN.md` for the full sequencing and honest
scoping statement; `PHASE_3_EXECUTION_PLAN.md` for the P0/P1 narrative.
Phase 2's original validation remains below, unchanged and still green.

## Latest quality gate (2026-08-05, after the security review pass)

```
backend:  pytest -q                         -> 152 passed
          ruff check app tests              -> clean
          mypy app --ignore-missing-imports -> clean (148 files)
frontend: tsc --noEmit / eslint             -> clean
          vitest run                        -> 59 passed
          next build                        -> succeeds (19 routes)
docker:   backend + frontend images rebuilt; all 5 services healthy
git:      4 commits this pass (e1f8bf5 P0+P1, efb2c28 Responsible AI,
          654ea12 Research Lab, e238b16 Security review) -- all on `main`,
          nothing staged/uncommitted
```

## Exact next unfinished task

Continuing the Final Beast Master sequence from
`FINAL_BEAST_MASTER_EXECUTION_PLAN.md` §2: **Milestone D (minimal role
dashboards)** is next, then Competition Mode, then presentation/research
docs, then a targeted premium UI pass, demo-dataset consistency,
production engineering, and final acceptance testing. Not yet started:
faculty/placement/recruiter/admin dashboards, `/competition` route, the
~20 presentation/research doc deliverables, and the full 95-item release
gate. All 5 roles (`student`/`faculty`/`recruiter`/`placement_staff`/
`administrator`) already exist seeded in the `roles` table with a working
`require_role()` RBAC primitive -- no new role infrastructure is needed,
only the dashboard routes themselves.

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
