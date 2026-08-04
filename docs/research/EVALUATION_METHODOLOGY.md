# Evaluation Methodology

## Experiment A — Routing strategy comparison

**Question**: does CARE's confidence-aware adaptive routing agree with a
rubric-labeled expectation more often than two fixed baselines (always
single-agent, always multi-agent)?

**Dataset**: `backend/app/evaluation/cases.py`, 8 curated cases spanning
easy/sufficient-evidence, missing-context, conflicting-evidence, ambiguous
low-confidence, high-disagreement-after-council, and
persistently-low-confidence scenarios — matching the dataset strategy in
`docs/06_EVALUATION_PLAN.md`. Each case carries an `expected_route` label
that is a **rubric stand-in, not a human-annotator-verified ground
truth** — documented as such directly in the dataset file.

**Method**: for each case, compute the route three ways —
`single_agent_fixed` (always `single_agent`), `multi_agent_fixed` (always
`multi_agent`), and `care_adaptive` (`decide_route()`, CARE's real,
unit-tested policy function) — and record whether each matches
`expected_route`. Agreement rate = matches / total cases, per variant.

**Reproduce**: `POST /research/experiments/routing` (authenticated), or
`python -m app.evaluation.run` from `backend/`.

## Experiment B — Graph traversal vs. vector-only retrieval

**Question**: for root-cause discovery, how much does having an explicit
concept-dependency graph help over pure text-similarity retrieval?

**Dataset**: every `Concept` row with at least one direct
`ConceptDependency` edge (14 in the current seeded taxonomy), paired with
its first direct prerequisite.

**Method**: for each concept, index its name+description into the vector
store (`SOURCE_TYPE_CONCEPT`, idempotent), then query with a synthetic
"I don't understand `<concept>`. `<description>`" prompt. Graph
traversal's accuracy is 1.0 by construction (it follows the exact stored
edge — this is stated as a methodology note in the API response itself,
not hidden). Vector-only accuracy is whether the expected prerequisite's
document ID appears in the top-3 reranked results from
`retrieval_service.search()` restricted to concept documents — the same
embedding (`HashingEmbeddingProvider`) and reranking (`SimpleReranker`)
stack the product uses everywhere else, not a weakened strawman.

**Reproduce**: `POST /research/experiments/graph-vs-vector`, or
`app.evaluation.graph_vs_vector.run_graph_vs_vector_evaluation()`.

## Calibration analysis

**Question**: does stated confidence match actual accuracy?

**Method**: pool every `EvaluationResult` row with a non-null
`accuracy_label` across all experiment runs (both A and B contribute
rows). Compute Brier score (mean squared error between confidence and the
binary correctness outcome), Expected Calibration Error (weighted-average
gap between mean confidence and empirical accuracy across 5 equal-width
reliability bins), and a high-confidence (≥0.8) error rate. Labeled
`preliminary` below 30 pooled results.

**Reproduce**: `GET /research/calibration[?run_id=...]`, or
`app.evaluation.calibration.compute_calibration()`.

## What is deliberately not claimed

- No result here is a large-scale, human-reviewed benchmark. Every dataset
  is small and curated, and every report explicitly says so.
- Calibration numbers mix two structurally different experiments (routing
  agreement and retrieval accuracy) into one pool — a real methodological
  simplification, disclosed here rather than hidden, appropriate for a
  first-pass calibration module rather than a rigorous per-task analysis.
- No live-LLM-provider run is included (no API key available in this
  evaluation environment) — every number here is from the deterministic
  provider path.
