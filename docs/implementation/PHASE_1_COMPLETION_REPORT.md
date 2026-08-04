# Phase 1 Completion Report

Status: **Phase 1 vertical slice complete and verified — including a real
Docker Compose + PostgreSQL smoke test.** All 20 acceptance criteria pass.
Every criterion was exercised: automated tests, static checks, a live
end-to-end browser walkthrough of the golden path, and (as of the update in
"§12 — Docker/PostgreSQL validation") a full containerized run against real
Postgres, Redis, and Neo4j, including a container-restart persistence check.

## 1. Implemented features

### Backend (FastAPI + SQLAlchemy + Alembic)
- Config, structured JSON logging, consistent error envelope
  (`{"error": {code, message, details, request_id}}`) for `AppError`,
  `HTTPException`, validation errors, and unhandled exceptions.
- `/health` and `/health/ready` (DB connectivity check).
- Auth: register, login, refresh (rotating opaque refresh token in an
  httpOnly cookie, hashed at rest), logout (revocation), `/auth/me`.
  Passwords hashed with `bcrypt`. Access tokens are short-lived JWTs.
- RBAC: five seeded roles (student, faculty, recruiter, placement_staff,
  administrator); only the student experience is fully implemented, per
  spec. `require_role(...)` FastAPI dependency gates every student route.
- Onboarding: target role, career goal, timeline, self-assessed skills
  (each becomes a `SkillEvidence` row) — triggers the first Career Twin
  snapshot.
- Resume pipeline: PDF/DOCX/TXT upload, validation (type/size/non-empty),
  local-disk storage abstraction, deterministic section detection, deterministic
  skill extraction against the seeded taxonomy, per-section evidence
  strength — see `docs/implementation/RESUME_PARSING.md`.
- Job description pipeline: paste a JD, deterministic requirement extraction
  (skill/experience/education/responsibility, required vs. optional), then a
  deterministic resume↔JD skill match (matched/partial/missing, coverage,
  confidence, plain-language explanation that explicitly disclaims "not a
  hiring probability").
- Career Twin scoring engine: six readiness components, deterministic and
  versioned (`twin-v1`) — see `docs/implementation/CAREER_TWIN_SCORING.md`.
  Every recompute writes a snapshot + per-component rows + a `DecisionTrace`
  + an `AuditEvent` in the same transaction.
- Mission generation: deterministic rule picks the weakest actionable
  readiness component and generates one active mission tied to it (superseding
  any prior pending mission), with a "mark complete" endpoint.
- Dashboard aggregation service: one endpoint composing profile, latest twin
  snapshot, active mission, priority weakness, resume/JD status, recent
  evidence, recent twin updates, recent audit events, and a system-trust
  summary — the frontend does zero domain aggregation.
- Audit log endpoint (per-student, paginated).
- Deterministic demo seed command (`python -m app.seed.seed_demo`), reusing
  the real onboarding/resume/JD service functions rather than hand-crafting
  rows, so seeding exercises the same code path a real student does.

### Frontend (Next.js 16 App Router + TypeScript + Tailwind v4)
- Pages: landing, register, login, demo entry, onboarding, dashboard, Career
  Twin detail, resume upload, job-description match, settings.
- Hand-built shadcn/ui-style component system on Radix primitives (button,
  card, input, label, textarea, badge, progress, tabs, skeleton, empty-state,
  error-state, toaster).
- Dashboard sections: personalized welcome, overall readiness, Career Twin
  confidence, target role, today's mission, skill radar + per-component
  cards, priority weakness, recent evidence, recent Twin updates, resume
  status, job-description match status, quick actions, system trust
  indicator — all from `/api/v1/dashboard`, no hard-coded or random values.
- React Query for server state, react-hook-form + Zod for form/schema
  validation, sonner for toasts.
- Auth: access token in memory + localStorage mirror; refresh token in an
  httpOnly cookie; automatic one-shot refresh-and-retry on 401.
- Dark/light theme via a `.dark` class toggle (persisted, no-flash inline
  script), fully responsive (sidebar collapses to a hamburger menu on
  mobile), loading skeletons, empty states, error states with retry, and
  labeled/keyboard-accessible form controls throughout.

### Infra
- `docker-compose.yml`: postgres (pgvector), redis, neo4j, backend, frontend,
  with healthchecks and a named volume for uploaded resumes.
- `backend/Dockerfile`, `frontend/Dockerfile` (multi-stage, Next.js
  standalone output).
- Cross-platform scripts in `scripts/` (PowerShell + POSIX pairs):
  `start_infrastructure`, `start_backend`, `start_frontend`,
  `start_full_stack` (Docker, everything), `migrate`, `seed_demo`.

## 2. Important architectural decisions

See `docs/implementation/PHASE_1_EXECUTION_PLAN.md` for the full writeup.
Highlights:

- **Cross-dialect DB layer.** Custom `GUID`/`JSONBType` SQLAlchemy
  `TypeDecorator`s emit native Postgres `UUID`/`JSONB` in Docker/production
  and portable `CHAR(36)`/`JSON` on SQLite. This sandbox has no
  Docker/Postgres available, so the **entire backend test suite runs against
  real SQLite databases created by running the actual Alembic migrations**
  (not `create_all`) — meaning migration correctness is verified on every
  `pytest` run, not just in Docker.
- **Career Twin scoring** is a pure, versioned, documented function with no
  LLM call — see `CAREER_TWIN_SCORING.md`. Components with zero evidence are
  stored as `insufficient_evidence`, never a fabricated number.
- **Resume/JD parsing adapters.** `resume_parser.py` / `jd_extractor.py`
  expose plain functions with no FastAPI/DB coupling, so a future LLM-backed
  implementation can replace them without touching the calling services.
- **Auth token storage trade-off.** Access token in `localStorage` is a
  known Phase 2 hardening item (documented, not hidden) — acceptable for a
  Phase 1 foundation.

## 3. Database migrations

Located in `backend/alembic/versions/`:

1. `788d1325f003_phase1_initial_schema.py` — full Phase 1 schema (20 tables:
   users, roles, user_roles, refresh_tokens, student_profiles, career_goals,
   target_roles, skills, student_skills, skill_evidence, resumes,
   resume_sections, resume_skills, job_descriptions, job_requirements,
   career_twin_snapshots, readiness_components, learning_missions,
   decision_traces, audit_events). Includes a deferred FK
   (`student_profiles.primary_target_role_id → target_roles.id`) added via
   `ALTER TABLE` after both tables exist, to break the natural
   `student_profiles ↔ target_roles` cycle.
2. `2e021960668e_seed_reference_roles_and_skills.py` — data migration
   seeding the 5 RBAC roles and a 55-entry skill taxonomy (used by both
   resume parsing and JD extraction). This is reference data, not demo data,
   so it ships as a migration and is present in any freshly migrated
   environment — registration works immediately after `alembic upgrade
   head`, with no seed script required.

Both migrations were verified: `upgrade head` → `downgrade base` → `alembic
check` (no drift between models and migrations) on SQLite, **and separately
`upgrade head` / `current` / `check` against a real containerized PostgreSQL
16 instance** — see §12. The Postgres run caught and fixed a real bug (a
UUID/JSONB column-type mismatch in the reference-data migration) that SQLite's
loose typing had silently masked; see §12 for details.

## 4. API routes (`/api/v1` prefix)

```
GET    /health
GET    /health/ready
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
GET    /auth/me
GET    /students/me
POST   /onboarding
POST   /resumes
GET    /resumes/me
POST   /job-descriptions
GET    /job-descriptions
GET    /job-descriptions/{id}
GET    /job-descriptions/{id}/match
GET    /career-twin
GET    /career-twin/history
GET    /dashboard
GET    /missions/active
GET    /missions
POST   /missions/{id}/complete
GET    /audit
GET    /skills
```

OpenAPI docs live at `/docs` (Swagger UI) and `/redoc` when the backend is
running.

## 5. Frontend routes

`/`, `/register`, `/login`, `/demo`, `/onboarding`, `/dashboard`,
`/career-twin`, `/resume`, `/job-description`, `/settings`.

## 6. Tests executed and results

### Backend — `pytest` (SQLite, migrations run for real per test)

```
28 passed in ~8s
```

Coverage: health/readiness, auth (register/login/refresh/logout/me,
duplicate email, weak password, wrong password, unauthenticated access),
RBAC (`require_role` allow/deny, missing student profile), onboarding
(happy path, unauthenticated, invalid seniority), resume upload (DOCX
parses sections/skills, unsupported type rejected, empty file rejected,
404 before upload), job description (requirement extraction, match with no
resume → all missing, match after resume upload → matched/partial/missing
classified correctly and idempotent on repeat reads), Career Twin scoring
(no-evidence snapshot is all-insufficient, evidence-backed snapshot scores
correctly and versions up), and the full dashboard happy path (onboarding →
resume → JD → dashboard reflects everything, mission completion, audit log,
skills catalog).

Static checks: `ruff check` — clean. `mypy --ignore-missing-imports` — clean
(0 errors across 66 files).

### Frontend

```
tsc --noEmit        -> clean
eslint               -> clean
vitest run           -> 16 passed (3 files: zod schemas, register page, login page)
next build           -> succeeds (13 static routes)
```

Component tests cover the two authentication forms end to end (validation
errors, successful submit + navigation, server-error handling) plus the
Zod schemas used across onboarding/JD forms.

### Manual end-to-end verification (real browser, both servers running)

Performed live in Chrome against the actual running backend + frontend, not
mocked: registered a new student → completed onboarding (target role +
self-assessed skill) → dashboard showed a real first Career Twin snapshot
with `insufficient_evidence` on every component except the one with
self-assessment evidence, and a generated mission → uploaded a plain-text
resume → 9 skills detected, sections parsed, dashboard/Twin updated to
version 2 → added a job description → 75% coverage with correct
matched/partial/missing classification, Twin updated to version 3 (93%
overall) → verified light/dark theme toggle renders correctly on every
page visited. No console errors, no broken buttons, no fabricated numbers —
every score on screen traced back to a real evidence row.

### Migration tests

Exercised implicitly on every backend test run (see above) plus explicitly
verified: `upgrade head`, `downgrade base`, `alembic check` (no drift) — all
clean on SQLite.

## 7. Exact commands to run the system

### Option A — native (fastest local loop; what was used to build and verify this phase)

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env      # edit DATABASE_URL if not using Docker Postgres (see comments)
alembic upgrade head
python -m app.seed.seed_demo
uvicorn app.main:app --reload   # http://localhost:8000, docs at /docs

# Frontend (separate terminal)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev              # http://localhost:3000
```

Or via the provided scripts: `scripts/start_infrastructure.{ps1,sh}` (docker
postgres/redis/neo4j only), `scripts/start_backend.{ps1,sh}`,
`scripts/start_frontend.{ps1,sh}`, `scripts/migrate.{ps1,sh}`,
`scripts/seed_demo.{ps1,sh}`.

### Option B — fully containerized

```bash
scripts/start_full_stack.ps1   # or .sh — docker compose up --build
```

Runs postgres, redis, neo4j, backend (migrates + seeds the demo student on
every start), and frontend. Frontend at http://localhost:3000, API at
http://localhost:8000.

### Tests

```bash
cd backend && pytest -q && ruff check app tests && mypy app --ignore-missing-imports
cd frontend && npx tsc --noEmit && npm run lint && npm test && npm run build
```

## 8. Demo credentials

```
Email:    demo.student@careerpilot.ai
Password: DemoPass!2026
```

Seeded via `python -m app.seed.seed_demo` (idempotent — safe to rerun before
a presentation). The seeded student ("Aanya Sharma") has a completed
onboarding, a parsed resume, a matched job description with an intentional
gap (Kubernetes missing, Communication only self-assessed) so the priority
weakness / mission / role-alignment story is visible immediately without
any manual setup during a demo. Or use the `/demo` page in the frontend for
a one-click sign-in.

## 9. Known non-blocking limitations

- **Redis and Neo4j** are provisioned in `docker-compose.yml`, verified
  healthy and reachable in the Docker smoke test (§12), but nothing in the
  Phase 1 code path reads from them yet — they're staged for Phase 2
  (GraphRAG, caching), per the brief.
- **Faculty/recruiter/placement/administrator roles** exist in the RBAC
  model and are seeded, but have no dashboards — intentional per the Phase 1
  scope ("Only the Student experience must be fully implemented").
- **Assessment readiness** always reports `insufficient_evidence` — there is
  no assessment module yet (Phase 2). This is a true statement, not a
  placeholder.
- **Access token in `localStorage`** (mirrored from memory) rather than a
  fully cookie-only auth flow — documented trade-off, flagged as a Phase 2
  hardening item.
- **No rate limiting middleware wired in yet** — FastAPI/Starlette makes this
  straightforward to add (e.g. `slowapi`) in Phase 2; not implemented in
  Phase 1.
- Two Next.js Turbopack dev warnings unrelated to app code were resolved
  (`agentRules: false` in `next.config.ts` to stop it from regenerating its
  own `AGENTS.md`/`CLAUDE.md` in `frontend/` on every `next dev`).

## 10. Acceptance criteria checklist

1. System starts locally — ✅ (native and Docker paths both provided; native path verified live; Docker path verified in §12)
2. Migrations execute successfully — ✅ (verified up/down/check on SQLite **and** up/current/check against real Postgres 16 in Docker, §12)
3. Register — ✅ (tested + verified live in browser)
4. Login — ✅ (tested + verified live in browser; also verified via `curl` against the Postgres-backed Docker backend, §12)
5. Refresh — ✅ (tested)
6. Logout — ✅ (tested)
7. Onboarding persists — ✅ (tested + verified live)
8. Resume upload + parse — ✅ (tested + verified live, real file, real skill/section extraction)
9. Job description add + parse — ✅ (tested + verified live)
10. Resume/JD evidence stored — ✅ (SkillEvidence rows, visible in dashboard evidence feed)
11. Career Twin snapshot from evidence — ✅ (tested + verified live, versioned, explained; re-verified against Postgres in §12)
12. Dashboard data from backend APIs — ✅ (zero hard-coded/random values; single aggregation endpoint; re-verified against Postgres in §12)
13. Seeded demo data loads — ✅ (idempotent seed command, verified via live login + dashboard, and re-verified idempotent against Postgres in §12)
14. Tests pass — ✅ (28/28 backend, 16/16 frontend)
15. Type checking passes — ✅ (mypy clean, tsc clean)
16. Linting passes — ✅ (ruff clean, eslint clean)
17. API documentation loads — ✅ (`/docs`, `/redoc`; re-verified served from the Docker container in §12)
18. README instructions accurate — ✅ (commands match what was actually run in this session)
19. No critical button or route broken — ✅ (verified live: all nav links, forms, upload, mission-complete, theme toggle)
20. Completion report created — ✅ (this document)

## 12. Docker / PostgreSQL validation (post-sandbox smoke test)

A real Docker Desktop environment became available after the initial Phase 1
build (which had no `docker` binary). This section documents the first real
`docker compose` run against actual Postgres/Redis/Neo4j, the two bugs it
found, and the fixes.

### Bug 1 — backend image failed to build

**Error:**
```
Multiple top-level packages discovered in a flat-layout: ['app', 'alembic']
```

**Root cause:** `backend/pyproject.toml` had no `[build-system]` table and no
explicit `[tool.setuptools.packages.find]` config. Setuptools' flat-layout
auto-discovery scans every top-level directory for importable packages and
found both `app/` (the real package) and `alembic/` (migration scripts, not
meant to be installed as a package) as candidates, and refuses to guess.
This only surfaces on a clean `pip install .` in a fresh image — it never
appeared in the dev venv because that was set up with `pip install -e .`
before `alembic/` existed in its current form, and the stale `.egg-info`
metadata masked it locally.

**Fix** (`backend/pyproject.toml`):
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]
exclude = ["alembic*", "tests*"]
```
This installs only `app` and its subpackages (all of which already had the
necessary `__init__.py` files — verified, no changes needed there). Alembic's
migration files still ship in the image because `backend/Dockerfile` already
had an explicit `COPY alembic ./alembic` step, independent of what gets
`pip install`ed — the CLI tool discovers migrations by path, not by import.

### Bug 2 — reference-data migration failed against real Postgres

**Error** (during `alembic upgrade head` inside the container, second
migration):
```
psycopg.errors.DatatypeMismatch: column "id" is of type uuid but expression is of type character varying
LINE 1: INSERT INTO roles (id, name, description) VALUES ($1::VARCHA...
```

**Root cause:** `2e021960668e_seed_reference_roles_and_skills.py` built its
`sa.table(...)` proxies with generic `sa.column("id", sa.String())` and
`sa.column("aliases", sa.JSON())`, instead of the actual model column types
(`app.core.types.GUID` / `JSONBType`). On SQLite this is invisible — SQLite
doesn't enforce column types, so a string bind into a "UUID" column just
works. On real Postgres, `roles.id`/`skills.id` are native `uuid` columns;
`bulk_insert` bound the id values as `VARCHAR` and Postgres refused the
implicit cast. This is exactly the class of bug the cross-dialect type layer
was built to prevent elsewhere — it was simply missed in this one migration's
raw table proxies, which don't go through the ORM models.

**Fix**: import and use the real types in the migration:
```python
from app.core.types import GUID, JSONBType
...
roles_table = sa.table("roles", sa.column("id", GUID()), ...)
skills_table = sa.table("skills", sa.column("id", GUID()), sa.column("aliases", JSONBType()), ...)
```
`GUID.process_bind_param` returns a plain string for the Postgres branch, but
because the column is now correctly typed as `GUID`/`PG_UUID` at bind time,
SQLAlchemy's psycopg dialect adapts it correctly instead of forcing a
`::VARCHAR` cast. Verified with a full container rebuild: migrations now
apply cleanly against Postgres from an empty database.

### Docker Compose smoke test — results

```
docker compose down --remove-orphans
docker compose build --no-cache backend      # succeeds after Bug 1 fix
docker compose up --build -d
docker compose ps
```

All five services reached a healthy/running state:

| Service  | Status                          |
|----------|----------------------------------|
| postgres | healthy (`pg_isready`)           |
| redis    | healthy (`redis-cli ping` → PONG)|
| neo4j    | healthy (HTTP 200 on :7474)      |
| backend  | running, `/api/v1/health` → 200 |
| frontend | running, `/` → 200               |

Migration/seed validation, run inside the container against real Postgres:
```
docker compose exec backend alembic upgrade head     # applies both migrations cleanly
docker compose exec backend alembic current           # -> 2e021960668e (head)
docker compose exec backend alembic check              # -> "No new upgrade operations detected."
docker compose exec backend python -m app.seed.seed_demo   # idempotent re-run, succeeds
```

Functional verification against the Postgres-backed backend:
- `GET /api/v1/health` → `200 {"status":"ok",...}`
- `GET /docs` → `200`
- `GET /` (frontend) → `200`
- `POST /api/v1/auth/login` with demo credentials → `200`, valid JWT
- `GET /api/v1/dashboard` (authenticated) → real Career Twin data: version 3,
  34 evidence rows, overall score 0.809 — same evidence-backed shape verified
  earlier against SQLite, now confirmed against Postgres.
- **Persistence check**: `docker compose restart backend postgres`, waited
  for both to report healthy, then re-ran login + dashboard — returned the
  **same** Career Twin version (3), evidence count (34), and score (0.809),
  confirming data survives a container restart via the `postgres_data` named
  volume.

### Quality gate re-run after the fix (both stacks)

```
backend:  pytest -q                 -> 28 passed
          ruff check .              -> clean (also auto-fixed 20 pre-existing
                                        style findings in alembic/ files that
                                        had never been linted before — import
                                        order, PEP 604 `X | Y` type hints —
                                        unrelated to the two bugs above)
          mypy app                  -> Success: no issues found in 66 source files
frontend: npx tsc --noEmit          -> clean
          npm run lint              -> clean
          npx vitest run            -> 16 passed
          npm run build             -> succeeds (13 static routes)
```

The backend image was rebuilt a final time after the ruff auto-fix and
re-verified at `alembic current` → head, confirming the shipped image matches
the linted source.

### Outcome

Phase 1 is now validated end-to-end against the actual target stack
(PostgreSQL, Redis, Neo4j, containerized backend and frontend), not only
against the SQLite fallback used during initial development. No previously
"environment-limited" acceptance criterion remains open.

## 13. Phase 2 prerequisites

- Assessment module: new `Assessment`/`AssessmentAttempt`/`QuestionResponse`
  models, wired into `assessment_readiness`.
- GraphRAG: Neo4j schema + hybrid retrieval, replacing keyword-based
  resume/JD matching with a real CARE Engine routing decision.
- LLM-backed resume/JD parsing adapter implementing the same
  `extract_text`/`detect_sections`/`extract_requirements` interfaces, gated
  behind `PRIMARY_LLM_API_KEY`/`SECONDARY_LLM_API_KEY` with the current
  deterministic parser as an automatic fallback.
- Interview Arena, Experiment Lab, Trust Center detail view, Research
  Benchmark Lab (all currently empty scaffold packages under
  `backend/app/{interviews,experiments,graphrag,trust_center,care_engine}`).
- Harden auth: move the access token out of `localStorage`, add rate
  limiting, add CSRF protection for the cookie-based refresh flow.
