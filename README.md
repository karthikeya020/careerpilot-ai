# CareerPilot AI

**An Evidence-Grounded, Confidence-Aware Agentic Career Operating System**

CareerPilot AI maintains a persistent **Career Twin** for each student, diagnoses root causes through **GraphRAG**, dynamically routes tasks through the **CARE Engine**, generates autonomous improvement missions, conducts evidence-based interview evaluation, and simulates alternative learning paths.

## Competition Positioning

CareerPilot AI is not a collection of disconnected placement tools. It is a closed-loop Career OS that:

1. Observes student evidence.
2. Builds and updates a Career Twin.
3. Diagnoses weaknesses and root causes.
4. Selects the minimum sufficient AI reasoning path.
5. Generates a targeted intervention.
6. Reassesses the student.
7. Explains every score change.

## Flagship Innovations

- **Career OS** — central command center
- **Career Twin** — persistent, evidence-backed student model
- **CARE Engine** — Confidence-Aware Reasoning and Escalation
- **Career GraphRAG** — root-cause analysis over skills, concepts, questions, roles, companies, and resources
- **Autonomous Improvement Loop** — observe → diagnose → plan → teach → assess → reflect → update
- **Interview Arena** — voice interview with specialist evaluation and replay
- **Career Experiment Lab** — what-if learning path simulations
- **AI Trust Center** — evidence, confidence, agent agreement, and human-review signals
- **Research Benchmark Lab** — systematic comparison of architectures and retrieval strategies

## Current Status

- [x] Phase 0 competition blueprint
- [x] Product requirements frozen
- [x] System architecture defined
- [x] Core data model drafted
- [x] Knowledge graph schema drafted
- [x] CARE routing rules drafted
- [x] Evaluation plan drafted
- [x] Demo story frozen
- [x] **Phase 1 foundation implementation** — see `docs/implementation/PHASE_1_COMPLETION_REPORT.md`
- [x] **Phase 2 AI intelligence core** — see `docs/implementation/PHASE_2_COMPLETION_REPORT.md`

Phase 1 delivers a working vertical slice: register → log in → onboard → select a
target role → upload a resume → add a job description → view a Career OS
dashboard backed by a deterministic, evidence-traceable Career Twin, plus a
seeded demo account.

Phase 2 adds the full AI intelligence core on top of that foundation: a
provider-neutral AI layer (deterministic fake + live Anthropic adapter), the
CARE routing engine, 10 specialist agents, a Neo4j knowledge graph with a
relational fallback, hybrid vector+graph retrieval, an adaptive SQL/Python
assessment engine, a curated resource catalog, an autonomous improvement loop
(Observe → Diagnose → Plan → Teach → Assess → Reflect → Update Twin → Next
mission), and an AI Trust Center exposing every routing decision, agent run,
and Career Twin change explanation. The demo student now has a real weak-SQL-
JOIN evidence point that drives a live CARE → GraphRAG → mission → resource →
reassessment loop from the moment the seed script runs.

## Repository Structure

```text
careerpilot-ai/
├── frontend/               # Next.js/TypeScript Career OS UI
├── backend/                # FastAPI services, SQLAlchemy models, Alembic migrations
├── database/               # Schema notes (see database/README.md — Alembic is authoritative)
├── evaluation/             # Research datasets, metrics, experiments (Phase 2+)
├── docs/                   # Product, architecture, roadmap, demo, implementation notes
├── scripts/                # Setup, migration, and seed scripts (PowerShell + POSIX)
├── docker-compose.yml
├── CLAUDE.md               # Project constitution — permanent engineering rules
└── .env.example
```

## Quick Start (Docker — recommended, this is what the demo uses)

```bash
docker compose up -d --build
```

That's it — migrations, Neo4j graph seeding, and the demo student (real
completed interview, Experiment Lab scenarios, and a full Research Lab
ablation-suite run) all happen automatically on container boot. Open
http://localhost:3000/login and sign in with:

```
Email:    demo.student@careerpilot.ai
Password: DemoPass!2026
```

**One-click reset**: `docker compose restart backend` — the demo account
deletes and recreates itself with the same known-good state on every
backend boot; any other (non-demo) account's data persists normally.

**Offline / no paid AI provider**: no API key is required for any of the
above — every score-producing path (Career Twin scoring, CARE routing,
assessment grading, the simulation engine, speech-to-text for the seeded
interview) has a deterministic, offline default. See
`docs/security/PROMPT_INJECTION_DEFENSE.md` and `docs/presentation/
BACKUP_DEMO_PLAN.md` for the full offline/failure-recovery story.

**Full stack verification / clean rebuild**:
```bash
docker compose down -v          # drop volumes for a truly empty-DB test
docker compose build --no-cache
docker compose up -d
docker compose ps               # all 5 services should show healthy
curl http://localhost:8000/api/v1/health/dependencies
```

## Quick Start (without Docker, backend/frontend run separately)

See `docs/implementation/PHASE_1_COMPLETION_REPORT.md` for the full
manual walkthrough. Short version:

```bash
# Backend (from backend/)
py -3.10 -m venv .venv && .venv\Scripts\activate   # or python3.10 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # defaults to Docker Postgres; see comments for a SQLite-only local option
alembic upgrade head
python -m app.graphrag.run_seed
python -m app.seed.seed_demo
uvicorn app.main:app --reload

# Frontend (from frontend/, in another terminal)
npm install
cp .env.local.example .env.local
npm run dev
```

Then open http://localhost:3000 and either register a new account or use
`/demo` to sign in as the seeded demo student.

## Development Principle

> No random scores. Every important AI output must be linked to evidence, confidence, provenance, and a decision trace.

See `CLAUDE.md` at the repository root for the full list of permanent project rules.

## Next Milestone

**Phase 3:** Interview Arena, Career Experiment Lab, a native pgvector ANN
index, human-reviewed evaluation datasets, and a second live LLM provider —
see `docs/implementation/PHASE_2_COMPLETION_REPORT.md` for the full
prerequisite list.
