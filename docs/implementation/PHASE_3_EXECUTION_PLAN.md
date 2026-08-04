# Phase 3 Execution Plan — Competition Release

## 0. Initial validation (performed before writing this plan, not assumed)

Every Phase 1/2 claim in `PHASE_2_COMPLETION_REPORT.md` and
`CURRENT_CHECKPOINT.md` was independently re-run against the live repo
today (2026-08-04), not read and trusted:

| Check | Command | Result |
|---|---|---|
| Backend tests | `.venv/Scripts/python.exe -m pytest -q` | **89 passed**, 0 failed |
| Backend lint | `ruff check app` | clean |
| Backend types | `mypy app --ignore-missing-imports` | clean, 122 files |
| Frontend types | `npx tsc --noEmit` | clean |
| Frontend lint | `npm run lint` | clean |
| Frontend tests | `npx vitest run` | **40 passed**, 0 failed |
| Frontend build | `npm run build` | succeeds, 13 static routes |
| Migrations | `alembic current` | `298c98dafbbb (head)`, no drift |
| Docker stack | `docker compose ps` | all 5 services healthy |
| Backend health | `GET /api/v1/health` | 200 ok |
| Graph health | `GET /api/v1/graph/health` | `{"available": true}` |
| Frontend | `GET /` | 200 |
| Interview/Experiment scaffolds | `find app/interviews app/experiments` | confirmed empty (`__init__.py` only), exactly as documented |

**No blocking defects found.** Phase 1/2 is exactly as strong as claimed —
this plan starts from a genuinely clean, verified baseline, not a claimed
one. No repair work is needed before Phase 3 begins.

## 1. What Phase 3 actually requires

The Phase 3 brief (`CLAUDE.md` project prompt) specifies a very large
surface: a full voice-enabled multi-agent Interview Arena, a deterministic
Career Experiment Lab with a simulation engine, a Research Benchmark Lab
with six comparison studies plus ablations plus calibration analysis, a
Responsible AI Center, three role dashboards, a security review, a
performance pass, and a full documentation/presentation package — all
built on evidence-only, auditable, non-fabricated output, consistent with
Constitution rules 1–16.

This is realistically several weeks of engineering, not a single pass.
Building all of it in one uninterrupted burst risks exactly the failure
mode the Constitution forbids: shallow scaffolding presented as complete,
invented benchmark numbers, or UI that isn't backed by real evidence. So
this plan sequences the work into independently shippable, independently
testable increments, each ending in a real quality gate (tests + lint +
types + a working demo path) before the next begins — the same discipline
Phase 1 and Phase 2 followed.

## 2. Sequencing and priority

Ordered by demo narrative value (per `07_WINNING_DEMO_STORY.md` and the
"FINAL PRODUCT GOAL" 16-step flow) and by dependency — later increments
build on earlier ones:

### P0 — Interview Arena core loop (highest narrative value; nothing after step 9 of the product goal exists yet)
- Audio architecture: browser recording, upload, storage abstraction,
  `SpeechToTextProvider` interface (deterministic fallback + one live
  adapter), typed-answer fallback.
- Interview data model + migration: `Interview`, `InterviewQuestion`,
  `InterviewAnswer`, `InterviewEvaluation`, `InterviewEvidence`.
- CARE-routed interview agents: Supervisor, HR, Technical, Communication,
  Resume Evidence, JD Alignment, Critic, Consensus, Memory — CARE decides
  which subset runs per answer, not a fixed pipeline.
- Rubric-based evaluation (relevance/correctness/depth/structure/evidence/
  clarity/conciseness/professionalism/role-alignment/resume-consistency),
  resume-claim evidence checking with the required respectful
  classifications.
- Career Twin update path from interview evidence.
- Interview Replay screen (audio, transcript, timeline markers, scores,
  agreement, confidence, evidence links, mission link, Trust Center link).

### P1 — Career Experiment Lab
- Deterministic, versioned, tested simulation engine (heuristic model over
  current score, evidence quantity/reliability, dependency graph, target
  role importance, diminishing returns, time budget, uncertainty) —
  separated from any LLM call.
- Scenario input UI, before/after Twin comparison, mandatory
  "personalized scenario estimate" disclaimer.
- AI explanation layer on top of the deterministic numbers (never
  generating the numbers itself).

### P2 — Research Benchmark Lab
- Extend `app/evaluation/` with Experiments B–F (retrieval quality, memory
  ablation, reflection ablation, confidence calibration, deterministic vs.
  AI-assisted scoring, live vs. demo-mode latency/cost).
- Ablation run configs (CARE off, graph off, vector off, memory off,
  reflection off, consensus off) with reproducible commands.
- Calibration module (reliability bins, Brier score, ECE).
- Research dashboard UI rendering real generated result files (never
  hand-typed numbers).

### P3 — Responsible AI Center + role dashboards
- Responsible AI documentation page (scope, limits, human review, data
  controls, provenance, consent, explicit non-claims list).
- Faculty / Recruiter / Placement-cell prototypes behind RBAC, aggregation
  only, no invasive per-transcript access by default.

### P4 — Security, performance, demo hardening, docs/presentation, release gate
- Security review + threat model docs; fix anything critical/high found.
- Timeouts/retries/circuit breakers, structured logs, health/dependency
  status, request IDs.
- Full offline/degraded-mode hardening matrix from the brief.
- Full documentation set + presentation assets + polished demo dataset.
- Final acceptance run against the 30-item release quality gate.

## 3. Working discipline for every increment

- New Alembic migration for every model change (Constitution rule 11).
- Every AI-adjacent output validated by a Pydantic/Zod schema before
  storage or render (rule 10).
- Every score/recommendation traceable to stored evidence or explicitly
  `insufficient_evidence` (rules 1–2).
- Deterministic fallback for every external dependency (rule 13).
- Tests land with the code that needs them, not after (rule 12).
- Full quality gate (`pytest`, `ruff`, `mypy`, `tsc`, `eslint`, `vitest`,
  `next build`) re-run at the end of each increment, results reported
  verbatim — never summarized as "should pass."

## 4. Status

### P0 — Interview Arena core loop: complete (2026-08-04)

Built and verified, not just described:

- **Data model + migration**: `InterviewSession`, `InterviewQuestion`,
  `InterviewAnswer`, `InterviewEvaluation` (`backend/app/models/interview.py`,
  migration `ccca34eecf1f`), applied to both the local dev DB and the
  running Docker Postgres.
- **Audio architecture**: `backend/app/services/speech_to_text.py`
  (provider-neutral interface, deterministic-fixture provider, live OpenAI
  Whisper adapter gated behind `SPEECH_TO_TEXT_API_KEY`, never exercised by
  tests), audio storage via `storage.save_audio`, typed-answer fallback that
  the flow always accepts even when no audio is present.
- **Nine interview agents**: `CommunicationAgent` (deterministic transcript
  metrics -- word count, filler ratio, STAR detection, never infers emotion
  or honesty), `TechnicalAgent`, `HRAgent`, `ResumeEvidenceAgent` (resume-claim
  evidence classification with the required respectful wording),
  `JDAlignmentAgent`, plus the existing `CriticAgent`/`ConsensusAgent`/
  `MemoryAgent`/`SupervisorAgent` (dispatch table extended with an
  `interview_evaluation` eligible roster).
- **CARE orchestration** (`backend/app/services/interview_service.py`):
  evidence-driven routing per mode -- technical/HR answers with sufficient
  bank context go straight to `single_agent`; resume/role/company modes
  gather context first via `graphrag_agent`; a short/off-topic/ungrounded
  answer is honestly flagged `evidence_conflict=True` and escalates to
  `multi_agent` + `ConsensusAgent`, then `critic_reflection` on continued
  disagreement. Verified with real route diversity in
  `tests/test_interviews_api.py::test_care_routes_differ_between_confident_and_thin_answers`.
  Interview evidence feeds `SkillEvidence` (Communication + Technical
  components) and `recompute_twin` at session completion.
- **Interview Replay**: audio player, transcript with source label, timeline
  markers derived from real transcript features (never fabricated), rubric
  dimension scores, strengths/improvements, evidence checks, better-answer
  framework, Trust Center deep link.
- **API + frontend**: `/interviews/*` endpoints; `/interview` (mode select),
  `/interview/[sessionId]` (question flow with mic-permission handling +
  always-available typed fallback), `/interview/[sessionId]/replay`.

**Verification performed, not claimed:**
- Backend: 111/111 pytest passing (89 prior + 22 new), `ruff check app tests`
  clean, `mypy app --ignore-missing-imports` clean (132 files).
- Frontend: 48/48 vitest passing (40 prior + 8 new), `tsc --noEmit` clean,
  `eslint` clean, `next build` succeeds (2 new dynamic routes).
- **Live browser walkthrough** (not just automated tests): registered a
  real account, started a technical interview, submitted two typed answers,
  watched CARE evaluate each one live (route `single_agent`, agents
  `technical` + `communication`), completed the session, opened Interview
  Replay (transcript, timeline marker, dimension scores, better-answer
  framework all rendered correctly), confirmed the Trust Center showed both
  `interview_evaluation` decisions with full agent traces, and confirmed the
  Career Twin created its first snapshot from interview evidence alone
  (Technical 90%, Communication 100%, both citing "2 evidence items" with
  the exact deterministic scoring-formula explanation).
- Docker images for `backend` and `frontend` rebuilt and the full 5-service
  stack (`postgres`, `redis`, `neo4j`, `backend`, `frontend`) restarted and
  re-verified healthy with the migration at head (`ccca34eecf1f`) -- the
  Interview Arena is live on the standard demo ports (3000/8000), not only
  in a throwaway dev server.

**Known limitations, stated plainly:**
- Only 3 technical questions and a handful of HR/resume/role/company
  question templates are in the bank -- fine for a demo, not yet a large
  question set.
- `ResumeEvidenceAgent`'s v1 heuristic never emits
  `contradicted_by_uploaded_evidence` (no negation-aware logic yet) --
  documented in the agent's own docstring.
- No live speech-to-text key is configured in this environment, so the
  audio path is verified through its typed/deterministic-fallback behavior,
  not a real transcription; the provider interface and OpenAI Whisper
  adapter are implemented and gated cleanly behind a settings key.
- Communication filler-word detection is a fixed keyword list, not a
  language model -- documented as a heuristic in the agent's docstring.

### P1 — Career Experiment Lab + Simulation Engine: complete (2026-08-05)

Built and verified:

- **Deterministic, versioned simulation engine** (`backend/app/simulation/
  engine.py`, formula `sim-v1`, full writeup in
  `docs/implementation/EXPERIMENT_LAB_SIMULATION.md`): every number is a
  pure function of the student's current Career Twin, evidence quantity/
  quality/diversity, the concept-dependency graph, the student's own
  Career Twin history (real observed trend, not an invented one), and their
  most recent job description's stated requirements. Exponential
  diminishing-returns curve over hours, plus a second diminishing-returns
  effect from headroom (harder to gain near 1.0) and sequential
  sub-additive stacking when two allocations touch the same component. No
  number is ever computed by a model call.
- **LLM explains, never computes**: `ExperimentExplainerAgent` receives only
  the already-computed deltas and restates them in prose; its deterministic
  fallback (no API key) proves the fallback path can't fabricate a number
  either.
- **Scenario API**: skill + hours + activity type + target role + time
  horizon + mixed allocations (`POST /experiments/scenarios`), side-by-side
  current-vs-simulated comparison per component with confidence,
  uncertainty, assumptions, and evidence used, plus a dedicated
  `GET /experiments/compare` for the brief's own "20h SQL vs 20h DSA vs 20h
  communication" example.
- **Frontend**: `/experiment-lab` — scenario builder with dynamic
  allocation rows, live result card (current/simulated/confidence,
  per-component bars, assumptions, explanation, disclaimer), past-scenario
  list with comparison checkboxes, side-by-side comparison grid. The exact
  required disclaimer — *"Personalized scenario estimate—not a guaranteed
  outcome or hiring prediction."* — is rendered on every result and once
  statically on the page itself.

**Verification performed, not claimed:**
- Backend: 133/133 pytest passing (117 prior + 16 new: 10 engine + 6 API),
  `ruff check app tests` clean, `mypy` clean (139 files).
- Frontend: 53/53 vitest passing (50 prior + 3 new), `tsc --noEmit` clean,
  `eslint` clean, `next build` succeeds (`/experiment-lab` added).
- **Live browser walkthrough** against the rebuilt Docker/Postgres stack:
  ran "20h SQL" (Technical 60%→70%, +10pts, confidence 31%), "20h DSA"
  (Technical 60%→69%, +9pts), and "20h Communication" (Communication
  75%→81%, +6pts) against a real student's Career Twin, then compared all
  three side by side — assumptions, evidence-used counts, and the
  disclaimer all rendered correctly on every card.
- Docker images for `backend`/`frontend` rebuilt; migration head
  `957a79bda179`; all 5 services confirmed healthy.

Next up: P2 (Research Benchmark Lab + ablations + calibration).
