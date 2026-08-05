# Judge Q&A Preparation

Honest, direct answers to the questions judges are most likely to ask.

**"Is this just a wrapper around an LLM API?"**
No. The deterministic provider (used throughout this evaluation, zero API
keys) proves every score-producing path — Career Twin scoring, CARE
routing, the simulation engine, deterministic assessment grading — is a
real, versioned, unit-tested formula, not a model call. A live LLM can be
configured (`PRIMARY_LLM_API_KEY`) to improve prose quality (resume
insights, coaching explanations, interview-agent nuance), but it is never
the only source of a stored score. See `docs/implementation/CAREER_TWIN_SCORING.md`
and `docs/implementation/EXPERIMENT_LAB_SIMULATION.md` for the exact formulas.

**"How do you know your Career Twin scores are accurate?"**
We don't claim ground-truth accuracy — we claim *evidence-traceability and
calibrated uncertainty*. Every score links to the exact evidence that
produced it; every score below the stability threshold (fewer than 3
evidence items or fewer than 2 independent sources) is shrunk toward a
neutral prior and confidence-capped (`twin-v2` small-sample safeguard),
specifically so a single interview session can never masquerade as a
confidently established skill level.

**"Isn't this just checking keywords, not real understanding?"**
Some deterministic paths are keyword/rubric-based by design (documented
plainly, e.g. `TechnicalAgent`'s fallback grader) — a fake-provider
grading system must be honest about being a proxy, not a hidden claim of
true comprehension. When a live model is configured, grading quality
improves; the fallback never pretends to be more than it is.

**"What stops the AI from hallucinating a root cause?"**
GraphRAG's root-cause path is graph traversal over explicitly stored
`DEPENDS_ON` edges (Postgres is the source of truth, Neo4j mirrors it for
visualization) — not a model generating a plausible-sounding explanation.
Experiment B in the Research Lab measures exactly this: graph traversal
is 100% accurate by construction; a pure vector-similarity approach
(what a generic chatbot with basic RAG would do) is measurably less
reliable at surfacing the same causal fact.

**"How is this different from ChatGPT with a system prompt about
careers?"**
A generic chatbot has no persistent evidence model, no confidence
calibration, no routing logic, no audit trail, and would happily generate
a hiring-probability number if asked. CareerPilot structurally cannot —
there is no code path that produces one. The Research Lab quantifies the
architectural difference (routing strategy comparison, retrieval
comparison) rather than asserting it.

**"What happens if the AI provider or internet goes down during your
demo?"**
Nothing breaks. The deterministic provider is the *default*, not a
fallback bolted on afterward — every agent, every scoring path, every
simulation works fully offline. See `docs/security/../BACKUP_DEMO_PLAN.md`
and Phase 2's verified Neo4j fail/recover cycle.

**"Is student data safe? What about the interview audio?"**
See `docs/security/PRIVACY_MODEL.md` and `SECURITY_REVIEW.md`. Students
have real, working self-service controls: full data export, audio-only
deletion (keeps transcripts), and full account deletion (cascades through
every table). Password hashing (bcrypt), refresh-token rotation, httponly
cookies, and Redis-backed rate limiting on auth endpoints are implemented
and tested, not just described.

**"Could a recruiter see my data without permission?"**
No. The recruiter dashboard only lists students who explicitly toggle
`recruiter_visible` in Settings — an opt-in, not an opt-out, and the
recruiter view has no automatic hiring recommendation of any kind (Trust
Center-style evidence and confidence only).

**"What's not finished yet?"**
Told honestly: dependency vulnerability scanning wasn't run in this
environment; prompt-injection hardening (explicit "data, not instructions"
framing in agent system prompts) is designed but not yet applied, since
the default path is structurally immune (no live model call at all); the
research dataset is small and curated, explicitly labeled preliminary,
not a large human-reviewed benchmark; no recorded video, printed poster,
or physical stage rehearsal exists (text scripts do, clearly labeled as
scripts); a dedicated axe-core accessibility audit and full mobile-
breakpoint sweep across all 24 routes hasn't been run beyond manual
spot-checks. See `docs/implementation/FINAL_RELEASE_COMPLETION_REPORT.md`
for the complete limitations list.

**"Is the demo data real or faked for the presentation?"**
Real, produced by the same service layer a real student's actions call —
never hand-crafted rows. The seeded interview session ran through the
actual CARE-routed evaluation pipeline (one answer via a real audio
fixture, transcribed by a deterministic provider registered to that exact
audio's hash — not a fabricated transcript); the resume-claim evidence
check is a real `ResumeEvidenceAgent` call against the uploaded resume
text; the Experiment Lab scenarios are real `sim-v1` engine runs; the
Research Lab ablations are real calls to `ConsensusAgent`/`CriticAgent`/
`MemoryAgent`. Everything resets to this same real state on every backend
restart — there's no separate "demo mode" that computes differently from
what a real student sees.

**"How rigorous is the ablation study, really?"**
Honestly: small and preliminary, not a large benchmark — every seam
reports `preliminary: true`. What it is not is invented: all six seams
(CARE, graph retrieval, vector retrieval, Career Twin memory, reflection,
consensus) call the real production agent code and report real deltas,
including one finding that isn't flattering (`MemoryAgent`'s confidence
signal is currently a constant, not graded) — disclosed rather than
hidden, because an ablation study that only shows numbers that make the
system look good isn't a real ablation study.

**"Why does the Career Twin sometimes show 'insufficient evidence'
instead of a score?"**
Because Constitution rule 1 — every score must come from stored evidence.
A component with zero linked evidence gets `insufficient_evidence`, never
a fabricated placeholder number. This is deliberate, not a bug.

**"What's the business model / who pays for this?"**
See `BUSINESS_VALUE.md` for the institutional value proposition
(university career-services deployment, per-seat or per-cohort licensing)
— this prototype does not implement billing.
