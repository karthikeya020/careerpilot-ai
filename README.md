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

## Quick Start

See `docs/implementation/PHASE_1_COMPLETION_REPORT.md` for exact commands,
demo credentials, and what's implemented vs. deferred to Phase 2. Short version:

```bash
# Backend (from backend/)
py -3.10 -m venv .venv && .venv\Scripts\activate   # or python3.10 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # defaults to Docker Postgres; see comments for a SQLite-only local option
alembic upgrade head
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
