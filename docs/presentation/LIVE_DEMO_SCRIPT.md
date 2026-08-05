# Live Demo Script

Full walkthrough script for the complete competition demo. For time-boxed
variants, see `THREE_MINUTE_DEMO.md`, `SEVEN_MINUTE_DEMO.md`, and
`TWELVE_MINUTE_DEMO.md`.

## Setup (before judges arrive)

1. `docker compose up -d` — confirm all 5 services healthy (`docker compose ps`).
2. Open `http://localhost:3000/login` in a fullscreen browser window.
3. Have credentials ready: `demo.student@careerpilot.ai` / `DemoPass!2026`
   (resets to a known-good state on every backend restart).
4. Optional: log in once beforehand to warm the Next.js cache.

## Script

**1. Log in** (10s) — narrate: "This is a real student account, evidence
persisted in PostgreSQL, not mock data."

**2. Dashboard** (30s) — point at: Career Twin overall score + confidence
side by side (never one without the other), priority weakness, today's
mission, CARE activity card, Trust alert if present.

**3. Career Twin page** (45s) — walk through the six readiness components.
Point at a component with `insufficient_evidence` status: "we never
invent a score here — this is honest, not padded."

**4. Trust Center** (45s) — open a recent CARE execution. Walk through
route, routing factors, every agent invoked with its own confidence and
evidence citations, the GraphRAG badge (Neo4j vs. relational fallback).

**5. Assessment → Mission loop** (60s) — answer a question incorrectly on
purpose (or use one already answered). Show the mission that was
generated, the root-cause explanation, the recommended resource.

**6. Interview Arena** (90s) — start a technical or HR interview, submit a
typed (or recorded) answer, show the live evaluation: dimension scores,
strengths/improvements, CARE route, agents invoked. Open Interview Replay
— transcript, timeline markers, evidence checks, better-answer framework.

**7. Career Experiment Lab** (60s) — the demo account already has 4 real
scenarios seeded (SQL, Data Structures, Communication, a balanced 30h
mix) as a safety net, but for the live wow-moment, run "20 hours SQL"
then "20 hours Communication" fresh in front of judges and compare side
by side. Point at the disclaimer text.

**8. Research Benchmark Lab** (45s) — click "Run all 6 ablations" live in
front of judges (CARE, graph retrieval, vector retrieval, Career Twin
memory, reflection, consensus) — real numbers computed on the spot, not
pre-baked. Point at the honest "preliminary" labels and the memory
ablation's disclosed limitation (a real negative finding, not hidden).
Pre-seeded results from container boot are shown immediately even before
clicking, as a safety net.

**9. Responsible AI Center** (30s) — scroll the "never evaluates" list.
Point at the model/formula/policy version badges.

**10. Competition Mode** (optional closer, 60s) — `/competition`, press
`Space` through Opening → Closing for the cinematic recap, or use it as
the *entire* demo shell instead of steps 2-9 individually. All 14 steps
show real data with zero manual setup — the demo seed pre-populates
interview, experiment, and research history on every container boot, so
there is no "run this first or step 9 will look empty" caveat anymore.

## If something fails mid-demo

See `BACKUP_DEMO_PLAN.md`. The short version: every AI-adjacent feature
has a deterministic fallback that still produces a real, evidence-backed
result — a dropped Neo4j connection or missing API key degrades the
*label* ("relational fallback" instead of "neo4j"), never the demo.
