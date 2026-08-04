# Technical Differentiators

What makes CareerPilot AI a real system, not a themed chatbot skin.

## 1. Evidence-only scoring, structurally enforced

`career_twin/scoring.py::recompute_twin` is a pure function of stored
`SkillEvidence` rows. There is no code path where a score is written
without a linked evidence ID or an explicit `insufficient_evidence`
status. This isn't a policy — it's the only function in the codebase
allowed to write a `ReadinessComponent`, and no agent has write access to
it (Constitution rule 1).

## 2. A real confidence-aware router, not a fixed pipeline

CARE's `decide_route()` (`care_engine/policy.py`) is a pure, dependency-free
function, unit-tested against every branch (8 policy tests) and
integration-tested through the persisting engine (route diversity
confirmed live: a strong technical interview answer settles on
`single_agent`; a thin/off-topic answer escalates to `multi_agent` →
`critic_reflection`). Compare this to a system that always calls the same
prompt regardless of input quality.

## 3. Small-sample statistical safeguard (`twin-v2`)

A real, documented Bayesian-shrinkage-style correction: evidence-diversity
weighting, prior-weighted score shrinkage, and a hard confidence cap below
stability thresholds. Verified with 6 targeted tests (one strong answer,
several strong answers from one source, conflicting evidence, repeated
evidence from one source, and evidence from multiple independent sources)
plus a live demonstration: a real session that raw-scored 90%/100%
displayed as 60%/75% with an explicit low-sample notice once shipped.

## 4. Deterministic, versioned simulation engine

`simulation/engine.py` (`sim-v1`) never lets an LLM compute a readiness
gain. Diminishing returns via an exponential hours curve, a second
diminishing-returns effect via headroom scaling, role importance grounded
in the student's actual job description requirements (not a guess), and
historical learning response computed from the student's own prior Career
Twin trend when available. `ExperimentExplainerAgent` can restate the
numbers in prose but has no path to alter them — proven by its
deterministic fallback reproducing the same content with no live key.

## 5. Real graph-backed root-cause analysis with live-verified fallback

Neo4j traversal with a relational-database fallback returning identical
content, differently labeled. This was verified by literally stopping the
Neo4j container mid-session and confirming the app didn't crash and the
Trust Center correctly labeled the fallback (Phase 2). Experiment B in the
Research Lab then quantifies *why* this matters: graph traversal
guarantees the correct prerequisite; vector-only similarity search is
measurably less reliable at the same task.

## 6. A Trust Center with real, queryable decision records

Every CARE decision persists route, routing factors, every agent
invocation (with its own confidence, evidence citations, and inference
type — `deterministic_calculation` / `model_inference` / `extracted_fact`
/ `user_claim`, distinguished per Constitution rule 6), cost, latency, and
policy version. Not a log line — a first-class, queryable Postgres table
backing a real UI.

## 7. Honest research instrumentation, not marketing numbers

The Research Benchmark Lab runs real experiments on demand — CARE-adaptive
vs. fixed routing (agreement rate against a rubric), graph traversal vs.
vector-only retrieval (explicitly caveated methodology), and a calibration
module computing real Brier score / ECE from stored results, labeled
`preliminary` below 30 samples. No chart in this product renders a number
that wasn't computed from a real run.

## 8. Defense-in-depth security built and tested, not assumed

bcrypt password hashing, rotated/hashed refresh tokens, httponly cookies,
IDOR isolation tested across every ID-addressable resource (interview
sessions, experiment scenarios, CARE executions, job descriptions,
assessment attempts), Redis-backed rate limiting on auth endpoints
(verified against live Redis), upload size/type validation on both resume
and interview-audio paths. See `docs/security/SECURITY_REVIEW.md`.

## 9. Full test discipline across every layer

158 backend tests (unit, integration, API, authorization-isolation,
security-regression), 68 frontend tests (component, flow, accessibility-
relevant assertions), `ruff`/`mypy`/`tsc`/`eslint` all clean, a production
Next.js build succeeding with 24 routes. Every number in this document is
reproducible by running the commands in `README.md`.
