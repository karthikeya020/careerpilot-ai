# Ablation Guide

All six named ablation seams are now mechanically reachable, run for real
against the actual production agent code, and produce real numbers — no
seam in this list is "designed but not wired" anymore (that was true of
seams 4-6 in an earlier pass; see "History" below).

Run all six in one call:

```bash
POST /api/v1/research/experiments/ablations
```

Or from the Research Lab UI (`/research-lab`) — the "Run all 6 ablations"
button executes the exact same code path. The demo seed
(`app/seed/seed_demo.py`) also runs this suite once automatically, so a
fresh Docker boot already has real results stored before anyone clicks
anything.

Formula/dataset version: `ablation-v1`. Implementation:
`backend/app/evaluation/ablations.py` (seams 4-6; seams 1-3 reuse
`app/evaluation/run.py` and `app/evaluation/graph_vs_vector.py`, labeled
here rather than duplicated). Tests: `backend/tests/test_ablations.py`.

## 1. CARE disabled (fixed routing) vs. CARE enabled

`single_agent_fixed` and `multi_agent_fixed` are "CARE disabled"
configurations (a hardcoded route instead of `decide_route()`);
`care_adaptive` is CARE enabled. 8 curated cases.

Sample result (this pass): `single_agent_fixed` 12.5% agreement,
`multi_agent_fixed` 25.0%, `care_adaptive` 100.0% — with the rubric labels.

## 2. Graph retrieval disabled (vector-only) vs. enabled

Experiment B's `vector_only` variant never touches the concept-dependency
graph -- that condition *is* "graph retrieval disabled." 14 curated cases.

Sample result: graph-enabled 100.0% (by construction -- it follows a
stored edge), graph-disabled (vector-only) 50.0%.

## 3. Vector retrieval disabled (graph-only) vs. enabled

The same Experiment B, read from the other side: `graph_traversal` never
calls `retrieval_service.search()` -- that condition *is* "vector
retrieval disabled." Same 14 cases, same run, two honest interpretations
of one real measurement (the system only has these two retrieval
channels, so there's no separate experiment to build).

Sample result: vector-enabled 50.0%, vector-disabled (graph-only) 100.0%.

## 4. Career Twin memory disabled vs. enabled

`run_career_twin_memory_ablation()` compares a council's `ConsensusAgent`
confidence with and without one real `MemoryAgent.run()` vote, for a real
student profile. 3 curated council configurations.

**Honest finding, not a cherry-picked number**: `MemoryOutput.confidence`
is currently a fixed `1.0` ("memory retrieval succeeded") rather than a
graded measure of relevance or recency. Enabling memory therefore always
pulls consensus confidence toward 1.0 by an amount that shrinks as the
council grows (a 1-vote council shifts more than a 2-vote council). This
is a real, disclosed limitation of the current `MemoryAgent` design, not
smoothed over -- a future pass could grade memory's confidence by how
recent/relevant the retrieved history is, at which point this ablation
would show a case-by-case-varying effect instead of a uniform pull.

## 5. Reflection (critic) disabled vs. enabled

`run_reflection_ablation()` compares a council's raw mean confidence with
`CriticAgent.run()`'s adjusted confidence over the same claims. 4 curated
claim sets covering clean/grounded, one unsupported claim, two unsupported
claims, and low-confidence-but-cited.

Finding: the critic only penalizes claims that are both high-confidence
(>=0.5) and cite no evidence -- the clean-grounded case is untouched
(delta 0), the two-unsupported-claims case sees the largest penalty, and
the already-low-confidence case is untouched because neither claim
crosses the unsupported-confidence threshold that triggers an issue.

## 6. Consensus disabled vs. enabled

`run_consensus_ablation()` compares the raw mean of council vote
confidences with `ConsensusAgent.run()`'s disagreement-penalized
confidence, over 4 vote sets spanning low to extreme disagreement.

Finding: consensus confidence is never above the raw mean (disagreement
only ever penalizes), and the penalty grows monotonically with
disagreement -- near 0 in the low-disagreement case, largest in the
extreme-disagreement case. Only the high- and extreme-disagreement cases
are flagged for escalation (matches the `_DISAGREEMENT_FLAG_THRESHOLD`
that routes real interview answers to `critic_reflection`).

## Preliminary, honestly

Every seam above reports `preliminary: true` -- all six case sets are
small (3-14 cases) and curated, not a large human-reviewed benchmark. The
numbers are real (computed by actually calling the production agents),
but the sample size does not support a confidence interval or a claim of
statistical significance. Re-running the suite reproduces the same
routing/retrieval numbers exactly (deterministic code paths); the
memory/reflection/consensus numbers are also exactly reproducible since
none of their inputs are randomized.

## History (for auditability)

An earlier pass shipped ablations 1-2 only, with 3-6 explicitly listed
here as "designed, not yet wired." That gap was closed in this pass:
`app/evaluation/ablations.py` was added, all six seams were wired to real
agent calls, `backend/tests/test_ablations.py` (12 tests) was added, and
the `/research-lab` UI grew a "Six-ablation comparison" card. Nothing
above claims a result that wasn't actually computed by running the code
in this repository.
