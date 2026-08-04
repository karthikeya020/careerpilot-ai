# Research Contributions

CareerPilot AI is a product, but three pieces of it are genuine,
reproducible research contributions in their own right.

## 1. A small-sample safeguard for evidence-backed skill scoring

**Problem**: single-session evidence (e.g., a two-question mock interview)
can raw-score 90-100% on a skill component. Naively displaying that number
misrepresents a thin sample as an established fact.

**Contribution**: `twin-v2` combines three levers into one formula —
evidence-diversity weighting (distinguishing repeated evidence from one
source vs. independent corroboration), prior-weighted shrinkage (pulling
the *displayed score itself*, not just confidence, toward a neutral prior
in proportion to trust), and a hard confidence cap below stability
thresholds. Documented in `docs/implementation/CAREER_TWIN_SCORING.md`
"Small-sample safeguard," tested against 5 distinct scenarios (one strong
answer, several strong answers from one source, conflicting evidence,
repeated evidence from one source, evidence from multiple independent
sources), each producing a materially different, correct outcome.

**Reproducibility**: `backend/tests/test_career_twin_small_sample_safeguard.py`.

## 2. Structured-graph vs. vector-only retrieval for root-cause discovery

**Problem**: "why is a graph better than plain RAG" is usually asserted,
rarely measured.

**Contribution**: Experiment B (`app/evaluation/graph_vs_vector.py`) builds
a real curated dataset from the concept-dependency graph (concept →
first-direct-prerequisite pairs) and measures, for each pair, whether pure
vector similarity search (over indexed concept descriptions, same
embedding/reranking stack the product uses everywhere else) surfaces the
correct prerequisite for a query about the concept the student missed.
Graph traversal's accuracy is 100% by construction (explicitly stated, not
hidden) — the paper-relevant number is the vector-only measurement, which
is real and can come out anywhere.

**Reproducibility**: `POST /research/experiments/graph-vs-vector`, or
`backend/tests/test_research_lab_api.py::test_graph_vs_vector_experiment_is_real_and_labeled_preliminary`.

## 3. CARE: confidence-aware adaptive routing vs. fixed strategies

**Problem**: most "multi-agent" systems either always call one agent or
always convene a council, regardless of whether the evidence justifies it.

**Contribution**: `decide_route()` is a pure, fully-specified policy over
`RoutingFactors` (evidence count/quality/conflict, agent confidence,
disagreement, risk level) implementing the exact table in
`docs/05_CARE_ENGINE_SPEC.md`. Experiment A compares three strategies
(always single-agent, always multi-agent, CARE-adaptive) against a
curated rubric-labeled case set, computing a real agreement rate per
strategy — not asserted, computed on every run.

**Reproducibility**: `POST /research/experiments/routing`, or
`backend/app/evaluation/run.py` / `run_evaluation()`.

## Limitations, stated plainly (not hidden)

- All three datasets are small and curated (8-16 cases), explicitly
  labeled `preliminary` wherever sample size is under 30 — never presented
  as a large-scale benchmark.
- Experiment A's "expected route" labels are a rubric stand-in
  (documented in `app/evaluation/cases.py`), not human-annotator-verified
  ground truth.
- No live-LLM-provider comparison was run in this environment (no API key
  available) — all research results here are from the deterministic
  provider path.

See `docs/research/EVALUATION_METHODOLOGY.md` and
`docs/research/FINAL_RESULTS_SUMMARY.md` for the full writeup and results.
