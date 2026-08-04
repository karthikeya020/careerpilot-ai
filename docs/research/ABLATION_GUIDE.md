# Ablation Guide

What's mechanically reachable today, run via real code paths, plus what's
designed but not yet wired into an automated ablation harness — stated
honestly rather than claimed complete.

## Reachable today

### CARE disabled (fixed routing) vs. CARE enabled

Already Experiment A's core design: `single_agent_fixed` and
`multi_agent_fixed` *are* "CARE disabled" configurations (a hardcoded
route instead of `decide_route()`); `care_adaptive` is CARE enabled.

```bash
POST /api/v1/research/experiments/routing
```

### Graph disabled (vector-only) vs. graph enabled

Experiment B directly implements this: the vector-only condition never
touches the concept-dependency graph at all.

```bash
POST /api/v1/research/experiments/graph-vs-vector
```

### Neo4j graph store disabled (relational fallback)

Not an "ablation" in the research sense, but a real, live-tested
degraded-mode comparison: stop the Neo4j container and confirm
`graph_source` in a root-cause response switches from `"neo4j"` to
`"relational_fallback"` with identical path content (verified in Phase 2,
§18.3 of `PHASE_2_COMPLETION_REPORT.md`).

```bash
docker compose stop neo4j
curl http://localhost:8000/api/v1/graph/root-cause/<question_id>
docker compose start neo4j
```

## Designed, not yet wired into an automated harness

These are real, inspectable code seams — a future pass can drive them
through the same `EvaluationResult` pipeline Experiments A/B use — but no
automated ablation currently runs them and reports a number. Listed
honestly as **not done**, not claimed:

| Ablation | Where the seam is | What's missing |
|---|---|---|
| Memory disabled vs. enabled | `MemoryAgent` invocation in `interview_service._multi_agent_step` | `MemoryAgent`'s output is currently informational only (not a consensus vote) — disabling it produces *no measurable output difference* today, which is itself a real, honestly-reportable finding, not yet formalized as an experiment |
| Reflection disabled vs. enabled | `care_engine.policy.decide_route`'s `critic_reflection` branch | No harness currently forces a case through `critic_reflection` and diffs confidence before/after `CriticAgent` |
| Consensus disabled vs. enabled | `ConsensusAgent` in `interview_service._multi_agent_step` | No harness compares raw mean-of-votes vs. `ConsensusAgent`'s disagreement-penalized confidence |
| Reranking disabled vs. enabled | `SimpleReranker` in `retrieval_service.search` | No harness compares raw cosine-similarity ranking vs. reranked ranking |
| Evidence-diversity weighting disabled vs. enabled | `career_twin/scoring.py`'s `diversity_factor` | Formula constant, not currently parameterizable without a code change |
| Confidence safeguard disabled vs. enabled | `twin-v2`'s `LOW_SAMPLE_CONFIDENCE_CAP` | Same — a real ablation would temporarily set the cap to 1.0 and re-run the 6 safeguard tests to show the *pre-safeguard* behavior for comparison |

## Recommended next step

Extend `app/evaluation/` with an `ablations.py` module that accepts a
`AblationConfig` (booleans for each seam above), monkeypatches or
parameterizes the relevant constant/branch, and re-runs Experiments A/B
under each configuration — producing a real before/after comparison table
instead of the qualitative seam-by-seam description above.
