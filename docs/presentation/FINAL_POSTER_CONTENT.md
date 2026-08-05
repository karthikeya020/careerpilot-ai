# Final Poster Content

Content and layout guidance for a physical or digital poster. Designed to
be understood in 30 seconds from 6 feet away — see "30-second test" at
the bottom before printing. This supersedes `POSTER_CONTENT.md` as the
presentation-day version; that file remains as a longer-form reference.

**This is text content and layout guidance only — no physical poster has
been printed.** Producing the artifact requires a human with design/print
tools and is out of scope for this pass. See "Manual actions" in
`PRESENTATION_DAY_RUNBOOK.md`.

---

## Layout (recommended: 3-column, portrait, A0/36"×48")

```
┌─────────────────────────────────────────────────┐
│  HEADLINE (full width, top)                      │
├───────────────┬───────────────┬─────────────────┤
│  PROBLEM       │  SOLUTION      │  ARCHITECTURE   │
│  (col 1)       │  (col 2, hero) │  (col 3)        │
├───────────────┼───────────────┼─────────────────┤
│  INNOVATION 1  │  INNOVATION 2  │  INNOVATION 3   │
├───────────────┴───────────────┴─────────────────┤
│  RESEARCH RESULTS (full width, large numerals)    │
├───────────────┬───────────────────────────────────┤
│  RESPONSIBLE AI│  IMPACT                          │
├───────────────┴───────────────────────────────────┤
│  QR / DEMO (full width, bottom)                   │
├───────────────────────────────────────────────────┤
│  CLOSING STATEMENT (footer band)                  │
└─────────────────────────────────────────────────┘
```

---

## Headline

**The Career Operating System That Shows Its Work**

*(Sub-line, smaller)* Every score traced to evidence. Every
recommendation explained. Nothing invented.

---

## Problem

Career tools give students a score with no explanation. No memory between
sessions. No traceable evidence. No honest uncertainty — just a number
and a shrug.

---

## Solution

CareerPilot AI builds a persistent, evidence-backed **Career Twin** for
every student — six readiness components, each with its own confidence
and evidence count, versioned every time new evidence arrives. A missed
question becomes a **graph-traced root cause**. A root cause becomes a
**mission**. A mission becomes new evidence. The loop never stops.

---

## Architecture

```
FastAPI · PostgreSQL (+pgvector) · Neo4j · Redis · Docker Compose
Next.js · TypeScript · React Query
```

- **CARE** (Confidence-Aware Reasoning Engine) — 6 routes, chosen
  per-decision from real evidence factors, not a fixed pipeline.
- **GraphRAG** — real Neo4j concept-dependency graph; verified relational
  fallback if the graph store goes down.
- **twin-v2** — evidence-diversity weighting + Bayesian shrinkage so one
  strong session never reads as an established skill.

---

## Three innovations

**1. Confidence-aware routing (CARE).** Most AI products pick one
strategy (always one model call, or always a fixed pipeline) and hope it
fits every case. CARE decides per-decision — one specialist when evidence
is sufficient, a council when it conflicts, a critic when the council
disagrees, a human when confidence stays low.

**2. Structured root-cause reasoning (GraphRAG).** Not retrieval-augmented
guessing — a real, traversable dependency graph. `student → failed
question → concept → missing prerequisite → role requirement`, every edge
a stored fact, not a similarity score.

**3. Deterministic simulation, not LLM invention.** The Experiment Lab's
"what if I studied X for Y hours" answer comes from a versioned formula —
diminishing returns, evidence diversity, historical trend — never a model
inventing a number. Labeled honestly: *"not a guaranteed outcome or hiring
prediction."*

---

## Research results

**CARE adaptive routing: 100%** agreement with expert judgment
*(fixed single-agent baseline: 12.5%)*

**Graph-traced root cause: 100%** accurate by construction
*(vector-only retrieval, the standard RAG approach: 50%)*

*(Large numerals for these four — they should be readable from across the
room. Sub-caption, small: "6 real ablations run against production agent
code, including one disclosed limitation, not hidden. Full methodology:
`docs/research/ABLATION_GUIDE.md`.")*

---

## Responsible AI

No hiring probability — ever computed, ever shown. No lie detection. No
public ranking. No inferred emotional or psychological state. Full
student control: export everything, delete interview audio, delete the
account. Every score traces to a named model, formula, and policy
version.

---

## Impact

**Students** get one system that remembers their evidence instead of
re-explaining themselves every session. **Universities** get defensible,
evidence-based cohort reporting instead of a vendor's opaque score.
**Recruiters** get opt-in-only evidence summaries with zero algorithmic-
hiring-discrimination exposure — the system structurally cannot make a
hiring call.

---

## QR / demo section

*(QR code placeholder — point it at the GitHub repository README or a
live demo URL, whichever the venue's network setup supports; do not
publish a URL here that isn't finalized.)*

**Try it yourself**: `docker compose up -d --build` — one command, fully
offline-capable, no API key required. Demo account: `demo.student@
careerpilot.ai`.

---

## Closing statement

**Your Career. Continuously Evolving.**

CareerPilot AI doesn't prepare a student for one interview — it
continuously learns how to guide every student toward their strongest
possible career, and it never has to lie to do it.

---

## The 30-second test

Before printing, stand 6 feet back and time yourself reading only the
headline, the three innovation titles (bold line, not the body text), and
the four large research numerals. If that alone doesn't communicate "what
is this and why is it credible" in 30 seconds, cut body text further —
the poster's job is to earn a closer look, not to explain the whole
product. Full explanation is what you're standing next to it for.
