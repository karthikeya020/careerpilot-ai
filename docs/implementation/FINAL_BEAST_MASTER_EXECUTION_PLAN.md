# Final Beast Master Execution Plan

## 0. Honest scoping statement

The "Beast Master" prompt specifies roughly 13 milestones (A-M), a 95-item
release gate, and 30+ documentation/presentation deliverables — realistically
several weeks of work for a team. This plan does not pretend that is
achievable in one pass with the same depth of independent verification
applied to P0/P1 (Interview Arena, Career Twin safeguard, Experiment Lab —
all live-browser-verified against Docker/Postgres). Instead it:

- Verifies current state honestly (below).
- Sequences remaining work by actual competition impact per unit of
  engineering effort, not by milestone letter order.
- Executes continuously, committing and checkpointing after each real,
  tested unit — never presenting code existence as a finished, verified
  feature.
- Explicitly marks what is genuinely out of reach in an automated coding
  session (recorded video, printed posters, live stage rehearsal in front
  of a physical audience, actual branding artwork) as **documentation and
  content deliverables**, not fabricated as completed physical assets.

## 1. Verified current state (2026-08-05, before this pass)

Re-run, not assumed:

| Check | Result |
|---|---|
| `docker compose ps` | 5/5 services healthy |
| `alembic current` | `957a79bda179` (head) |
| Backend `pytest -q` | 133 passed |
| Backend `ruff` / `mypy` | clean |
| Frontend `vitest run` | 53 passed |
| Frontend `tsc` / `eslint` / `next build` | clean, succeeds |
| Git | P0+P1 work committed (`e1f8bf5`) |

**Complete and verified**: auth/RBAC, onboarding, resume+JD intelligence,
Career Twin (`twin-v2`, small-sample-safeguarded), evidence ledger,
GraphRAG + relational fallback, hybrid retrieval, CARE (6 routes),
specialist agents, adaptive assessment, autonomous mission loop, Trust
Center, Interview Arena (voice/typed, 5 new agents, CARE-routed
evaluation, Replay), Career Experiment Lab (`sim-v1` simulation engine,
scenario comparison), initial research instrumentation
(`app/evaluation/`, Experiment A only).

**Confirmed present but unbuilt** (checked directly, not assumed): all 5
roles (`student`, `faculty`, `recruiter`, `placement_staff`,
`administrator`) already exist in the seeded `roles` table and
`require_role()` RBAC primitive — but no faculty/recruiter/placement/admin
API routes or UI exist yet. No Responsible AI Center route. No Research
Lab UI (only the CLI `app/evaluation/run.py` + Experiment A dataset).
No Competition Mode route. No `docs/security/*` files.

## 2. Sequencing (impact-per-effort order, not letter order)

1. **Responsible AI Center** (Milestone C) — self-contained, directly
   required by release-gate items 37/94, no dependency on unbuilt systems.
2. **Research Benchmark Lab** (Milestone B, scoped) — extends the existing
   `app/evaluation/` module with the ablation experiments that are
   mechanically reachable today (CARE on/off, graph on/off, memory on/off,
   reflection on/off) plus a calibration module, and a UI. Full 16-item
   metric/ablation matrix from the prompt is aspirational; ship what is
   genuinely computable from real code paths, label the rest
   `not yet implemented` rather than inventing numbers.
3. **Security review + hardening** (Milestone E) — real audit against the
   actual codebase, fix what's cheap and correct (rate limiting, upload
   validation, error-message leakage), document what's deferred honestly.
4. **Minimal role dashboards** (Milestone D) — faculty/placement/recruiter/
   admin, privacy-aware aggregates only, explicitly scoped small per the
   original Constitution ("should not distract from the student journey").
5. **Competition Mode** (`/competition`) (Milestone J) — guided stage
   wrapper around already-built, already-verified screens. Highest
   audience-facing payoff per engineering hour, because it reuses real
   working features rather than building new ones.
6. **Presentation + research + security documentation** (Milestone L) —
   text deliverables, cheap relative to payoff.
7. **Targeted premium UI pass** (Milestone H) — on the highest-visibility
   screens (dashboard, Career Twin, GraphRAG, Interview Replay, Experiment
   Lab, Trust Center), not a full ground-up design-system rebuild.
8. **Demo dataset consistency pass** (Milestone I) — one coherent seeded
   student story, verified to not contradict itself across pages.
9. **Production engineering + offline resilience** (Milestones F/G) — G is
   largely already satisfied (deterministic providers, relational graph
   fallback, typed-answer fallback all exist and are tested); add health/
   readiness endpoints and confirm the existing fallbacks under simulated
   failure. F gets a light pass (structured logging, request IDs) rather
   than a full observability stack, which is disproportionate for a demo
   release.

## 3. What will not be fabricated

- No recorded video, printed poster, or physical rehearsal — these need a
  human and real hardware. Scripts/content for them will be written as
  markdown deliverables; the artifacts themselves are out of scope for a
  coding session.
- No benchmark number without a real run behind it. Where the full ablation
  matrix isn't mechanically reachable in this pass, the Research Lab will
  say so rather than showing a fabricated chart.
- No claim of "tested" without an actual command run and its real output.

## 4. Status

In progress — see `CURRENT_CHECKPOINT.md` for the live "what's done / what's
next" record, updated after every milestone.
