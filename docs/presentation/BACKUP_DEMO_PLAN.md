# Backup Demo Plan

CareerPilot AI is designed so that most "failures" a judge might witness
are actually correct, labeled degraded-mode behavior — not a broken demo.
Recovery target: **under 15 seconds** for every scenario below.

## No internet / LLM provider outage

**What happens**: nothing breaks. The deterministic provider is the
*default* code path (used throughout this entire evaluation, zero API
keys configured) — every agent, every score, every simulation number
already comes from a real deterministic formula. A configured live
provider failing simply falls back (`FallbackChatProvider`) with
`is_fallback=True` recorded, silently to the demo audience.
**Recovery**: none needed — nothing to recover from.

## Speech-to-text provider outage / no microphone

**What happens**: `DeterministicSpeechToTextProvider` returns
`source="unavailable"` for unregistered audio; the interview flow
immediately accepts the typed-answer fallback, which was always visible
alongside the recording control — never a dead end.
**Recovery**: click into the typed-answer textarea, continue. **~2 seconds.**

## Microphone permission denied

**What happens**: `useAudioRecorder` sets `status="permission_denied"`,
the UI shows a clear message and keeps the typed-answer path fully usable.
**Recovery**: type the answer instead. **~2 seconds.**

## Neo4j outage

**What happens**: `is_graph_available()` returns false, GraphRAG falls
back to the relational concept-dependency table (same content, labeled
`graph_source: "relational_fallback"`). Verified live in Phase 2 by
stopping the Neo4j container mid-session — the backend did not crash, the
dashboard stayed functional.
**Recovery**: `docker compose restart neo4j` (if you want the graph badge
back) — not required for the demo to continue. **~10-15 seconds if done.**

## Redis outage

**What happens**: the rate limiter fails open (logs a warning, allows the
request) — authentication and every other feature keep working. No
caching layer currently depends on Redis being up.
**Recovery**: none needed for demo continuity;
`docker compose restart redis` if desired.

## PostgreSQL restart

**What happens**: on backend restart, the seeded demo account
(`demo.student@careerpilot.ai`) resets to its known-good state by design
(`seed_demo.py` runs on every backend boot) — this is a *feature* for
demo reliability, not data loss. Any other (non-demo) account's data
persists normally across restarts (verified in Phase 2).
**Recovery**: log back in. **~5 seconds.**

## Browser refresh mid-flow

**What happens**: every screen re-fetches from the API on mount (React
Query), so a refresh mid-interview or mid-experiment just re-renders the
current server state — no client-only state is load-bearing.
**Recovery**: none needed.

## Empty database (fresh install)

**What happens**: every list/aggregate screen shows a real, designed
empty state (never a crash) — `EmptyState` components throughout, an
`insufficient_evidence` status on every Career Twin component, a "run an
experiment above" prompt on the Research Lab.
**Recovery**: run `alembic upgrade head` then seed
(`docs/implementation/CURRENT_CHECKPOINT.md` "Demo credentials" section).

## Docker/container issue

**What happens**: `docker compose ps` shows which service is unhealthy.
**Recovery**: `docker compose restart <service>`, or
`docker compose up -d --build` for a full rebuild. **Full rebuild ~2 minutes** —
if this happens mid-demo, switch to the static screenshot flow
(`SCREENSHOT_CHECKLIST.md`) or narrate from `PROJECT_PITCH.md` while it rebuilds.

## Presenter skips a step / loses their place

**What happens**: `/competition` mode has an explicit step counter and
`R` (reset) always returns to the Opening slide — no risk of getting lost
in a nonlinear demo.

## Absolute last resort

If the entire stack is unusable, present from this documentation set
directly: `PROJECT_PITCH.md` (narrative), `TECHNICAL_DIFFERENTIATORS.md`
(depth), and `docs/implementation/FINAL_RELEASE_COMPLETION_REPORT.md`
(exact verified test/build results) are all real, honest artifacts that
can carry a Q&A session without a live system.
