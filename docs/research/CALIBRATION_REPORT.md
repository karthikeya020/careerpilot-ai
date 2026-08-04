# Calibration Report

See `docs/research/FINAL_RESULTS_SUMMARY.md` "Confidence calibration" for
the exact numbers from the most recent run. This document explains the
module and how to interpret it.

## What's being calibrated

Every `EvaluationResult` row written by Experiment A (routing agreement)
or Experiment B (retrieval accuracy) carries a `confidence` (0-1) and an
`accuracy_label` (`"match"` / `"mismatch"`). Calibration asks: when the
system says it's 90% confident, is it actually right about 90% of the
time?

## Metrics computed

- **Brier score**: mean squared error between confidence and the binary
  correctness outcome. 0 is perfect, 0.25 is what a constant 50%
  confidence gets you against a 50/50 outcome distribution, 1.0 is
  maximally wrong.
- **Expected Calibration Error (ECE)**: bins results into 5 equal-width
  confidence ranges, computes `|mean_confidence − empirical_accuracy|` per
  bin, and takes the count-weighted average across bins.
- **High-confidence error rate**: of results with confidence ≥ 0.8, what
  fraction were actually wrong. A well-calibrated system should see this
  stay low; a high value here means the system claims certainty it hasn't
  earned.
- **Reliability bins**: the raw per-bin (count, mean confidence, accuracy)
  data ECE is computed from — the same shape a reliability diagram plots.

## How to read the current result honestly

The most recent run (`FINAL_RESULTS_SUMMARY.md`) shows a real
overconfidence gap in the 80-100% bin: 94.3% mean confidence vs. 74.2%
empirical accuracy. Two structural reasons, both worth stating rather than
hiding:

1. **Experiment B's graph-traversal condition always reports confidence
   1.0** — it's confidence-by-construction (a deterministic edge lookup,
   not a probabilistic estimate), and it's `"match"` 100% of the time by
   definition. Pooling it into the same calibration analysis as
   Experiment A's genuinely uncertain routing decisions inflates the
   high-confidence bin's *count* without inflating its *error rate*
   equally — a real methodological wrinkle, disclosed in
   `EVALUATION_METHODOLOGY.md`.
2. **Experiment A's fixed-baseline variants** (`single_agent_fixed`,
   `multi_agent_fixed`) also report a confidence value even when their
   route obviously mismatches the rubric label on most cases — this
   correctly drags the calibration numbers down for those variants
   specifically, which is honest, not a bug.

## Preliminary threshold

Below 30 pooled results, every report is labeled `preliminary: true`.
This is a heuristic threshold (common in small-sample statistics
discussions, not derived from a formal power analysis for this specific
metric) — stated as a heuristic, not overclaimed as statistically
rigorous.

## Recommended next step

Compute calibration **per experiment** (via `run_id` filtering, already
supported by `GET /research/calibration?run_id=...`) rather than only
pooled, so Experiment A's genuinely-uncertain routing confidence isn't
averaged together with Experiment B's by-construction graph confidence.
