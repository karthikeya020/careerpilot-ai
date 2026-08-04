# Phase 1 Execution Plan

## Scope

Deliver the vertical slice defined in the Phase 1 brief: register → login → onboard →
select target role → upload resume → paste/upload job description → view a
Career OS dashboard backed by a deterministic, evidence-traceable Career Twin,
plus a seeded demo account. Roles beyond Student are modeled in the
authorization layer only (no dashboards yet).

## Key Architectural Decisions

1. **Database portability.** Production/Docker target is PostgreSQL 16 +
   pgvector, per `docker-compose.yml`. This sandbox has no Docker/Postgres
   available (`docker`/`psql` are not on PATH), so the backend uses two
   SQLAlchemy `TypeDecorator`s — `GUID` and `JSONBType` — that emit native
   `UUID`/`JSONB` on Postgres and portable `CHAR(36)`/`JSON` elsewhere. This
   lets the same models run against Postgres in Docker and against a SQLite
   file for local tests in this sandbox, with no behavior fork in business
   logic. Alembic migrations are authored/reviewed against the Postgres
   dialect since that's the deployment target.
2. **Auth.** Passwords hashed with `bcrypt` directly (no passlib, avoids its
   Windows/py3.14 wheel friction). JWT access tokens (short-lived, HS256) +
   opaque refresh tokens persisted in a `refresh_tokens` table (hashed at
   rest) so logout/revocation is a real DB operation, not just client-side
   token deletion.
3. **RBAC.** `Role` / `UserRole` many-to-many with five seeded roles
   (student, faculty, recruiter, placement_staff, administrator). A
   `require_role(...)` FastAPI dependency gates routes; only student-facing
   routes are fully implemented this phase.
4. **Resume/JD parsing.** Deterministic, rule-based extraction (regex section
   headers, keyword skill matching against a seeded `Skill` taxonomy). Built
   behind a small adapter interface (`ResumeParser`, `JDExtractor`) so a
   future LLM-backed implementation can be swapped in without touching
   callers — satisfies the "AI providers must be replaceable through
   adapters" rule even though Phase 1 has no live LLM call.
5. **Career Twin scoring.** A pure, versioned function
   (`SCORING_RULE_VERSION = "twin-v1"`) in `app/career_twin/scoring.py` that
   maps stored `SkillEvidence` rows into six `ReadinessComponent`s
   (resume, technical, communication, assessment, portfolio, role_alignment).
   Components with zero supporting evidence are stored as
   `status="insufficient_evidence"` rather than a fabricated number. Every
   run writes one `CareerTwinSnapshot` (versioned, diffed against the prior
   snapshot), a `DecisionTrace`, and an `AuditEvent`. Documented in
   `docs/implementation/CAREER_TWIN_SCORING.md`.
6. **Dashboard aggregation.** A single service composes profile, latest twin
   snapshot + components, resume/JD status, top evidence, mission, and audit
   feed into one response — the frontend never assembles domain logic
   client-side.
7. **Frontend data/auth.** Access token kept in memory (React context) +
   mirrored to `localStorage` for reload persistence (documented as a Phase 2
   hardening item — httpOnly cookie rotation is preferable); refresh token is
   an httpOnly cookie set by the backend. React Query for server state, Zod
   for form + API response validation, hand-built Tailwind component
   primitives in the shadcn/ui style (button, card, input, badge, progress,
   tabs, toast) rather than pulling the shadcn CLI, to keep the dependency
   surface small and auditable.

## Sequencing

1. CLAUDE.md constitution.
2. Backend core (config, DB session, logging, error envelope, health/ready).
3. Models + Alembic migration.
4. Auth + RBAC.
5. Onboarding/profile/target role.
6. Resume pipeline.
7. JD pipeline + matching.
8. Career Twin scoring.
9. Missions + dashboard aggregation + audit API.
10. Seed command.
11. Backend tests (pytest, SQLite-backed).
12. Frontend scaffold + design system.
13. Frontend pages (auth, onboarding, dashboard, twin, resume, JD, settings).
14. Frontend states/a11y polish.
15. Frontend typecheck/lint/tests.
16. Docker/infra completion.
17. Completion report.

## Known Constraint

This sandbox cannot run Docker, PostgreSQL, or Neo4j. Backend tests run
against SQLite through the portable type layer described above. Docker
Compose / Postgres / Neo4j paths are written and documented but not
exercised end-to-end in this session — flagged explicitly in the completion
report rather than claimed as verified.
