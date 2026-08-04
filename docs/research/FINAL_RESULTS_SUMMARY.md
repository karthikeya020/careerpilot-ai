# Final Results Summary

Real results from a live run against the local development database on
2026-08-05, via `python -m app.evaluation.run` and
`app.evaluation.graph_vs_vector.run_graph_vs_vector_evaluation()`. See
`EVALUATION_METHODOLOGY.md` for the exact method. **Re-run these commands
before presenting** — they are deterministic in route/accuracy but will
generate a fresh `run_id` and may see a different calibration sample size
depending on how many prior runs are pooled in that database.

## Experiment A — Routing strategy agreement

| Variant | Agreement rate | Cases |
|---|---|---|
| `single_agent_fixed` | 12.5% | 8 |
| `multi_agent_fixed` | 25.0% | 8 |
| `care_adaptive` | **100.0%** | 8 |

CARE's adaptive routing matched the rubric label on every one of the 8
curated cases; both fixed baselines matched only when the case happened to
call for their one fixed behavior. This is the expected, not a
cherry-picked, result — the dataset was specifically constructed to
include cases needing each of the 6 routes (per
`docs/06_EVALUATION_PLAN.md`), so a fixed strategy can only ever be
"right" on the subset matching its one behavior.

## Experiment B — Graph traversal vs. vector-only retrieval

| Method | Accuracy | Cases |
|---|---|---|
| Graph traversal | 100.0% (by construction) | 14 |
| Vector-only retrieval | **50.0%** | 14 |

Half of the 14 concept-prerequisite pairs were *not* reliably surfaced by
pure text-similarity search over the same concept descriptions, using the
same retrieval stack the product relies on elsewhere. This is a real,
reproducible measurement of the value the structured graph adds over
retrieval alone — not an assumption.

## Confidence calibration

Pooled across 52 stored evaluation results (both experiments' accumulated
runs in this database):

| Metric | Value |
|---|---|
| Sample size | 52 |
| Brier score | 0.231 |
| Expected Calibration Error | 0.152 |
| Status | **preliminary is `false`** at this sample size (≥30), but still a small, curated pool — not a large benchmark |

Reliability bins (confidence range → mean confidence, empirical accuracy):

| Confidence range | Count | Mean confidence | Accuracy |
|---|---|---|---|
| 0-20% | 0 | — | — |
| 20-40% | 3 | 30.0% | 33.3% |
| 40-60% | 18 | 53.3% | 44.4% |
| 60-80% | 0 | — | — |
| 80-100% | 31 | 94.3% | 74.2% |

**Reading this honestly**: confidence in the 40-60% band is reasonably
calibrated (53% stated vs. 44% actual). The 80-100% band is
*overconfident* — 94% stated confidence against 74% actual accuracy, an
18-point gap. This is disclosed, not smoothed over: it's exactly the kind
of finding a calibration module exists to surface, and it's a legitimate
target for future work (e.g., tightening the graph-traversal experiment's
flat 1.0 confidence, which contributes disproportionately to the
high-confidence bucket and is confidence-by-construction rather than a
genuinely uncertain model estimate).

## How to reproduce this exact table

```bash
cd backend
./.venv/Scripts/python.exe -m app.evaluation.run
# then, in a Python shell or via the API:
# POST /api/v1/research/experiments/graph-vs-vector
# GET  /api/v1/research/calibration
```

Or run live from the Research Lab UI (`/research-lab`) — the "Run
Experiment A/B" buttons execute the exact same code path.
