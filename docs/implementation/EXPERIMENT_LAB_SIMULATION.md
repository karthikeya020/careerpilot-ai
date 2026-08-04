# Career Experiment Lab Simulation Engine — Formula `sim-v1`

Implemented in `backend/app/simulation/engine.py`. Deterministic, no LLM
call, versioned via `engine_version` on every `ExperimentResult`. An LLM
(`ExperimentExplainerAgent`) may restate the engine's numbers as prose; it
is never given a path to compute or adjust them (Constitution-aligned
Prompt 3 rule: "Do not let an LLM invent readiness gains").

## Inputs

A scenario is a name, an optional target role, a time horizon, and 1-8
allocations of `(skill_name, activity_type, hours)`. The engine also reads,
per allocation:

- The student's current Career Twin (`CareerTwinSnapshot` +
  `ReadinessComponent` rows) — score, confidence, evidence count, evidence
  diversity per component.
- The concept-dependency graph (`ConceptDependency`) — how many other
  concepts depend on this skill's linked concept.
- The student's most recent `JobDescription`'s `JobRequirement` rows — is
  this skill actually required for the role they're targeting.
- The student's own Career Twin history (2+ snapshots) — has this
  component actually trended up or down for this specific student.

## Per-allocation formula

```
base_score        = current component score, or 0.5 (neutral prior) if insufficient evidence
effectiveness      = ACTIVITY_EFFECTIVENESS[activity_type]        # fixed table, default 0.7 if unrecognized
raw_gain           = MAX_GAIN_PER_ALLOCATION * (1 - e^(-hours / HOURS_DECAY_CONSTANT)) * effectiveness
headroom_factor    = 0.3 + 0.7 * (1 - base_score)                  # less room to grow near 1.0 -> smaller gain
role_importance    = 1.0 if required by the student's JD, 0.7 if JD exists but doesn't require it, 0.6 if no JD on file
role_factor        = 0.5 + 0.5 * role_importance
dependents_bonus   = min(1.15, 1 + 0.05 * count(concepts that depend on this skill's concept))
historical_multiplier = clamp(this student's own avg per-snapshot delta / BASELINE_DELTA_PER_SNAPSHOT, 0.7, 1.5)
                         -- or 1.0 if fewer than 2 prior snapshots exist for the component,
                         -- or 0.85 if the student's own trend has been flat/declining

gain = raw_gain * headroom_factor * role_factor * dependents_bonus * historical_multiplier
new_component_score = clamp(base_score + gain, 0, 1)
```

`MAX_GAIN_PER_ALLOCATION = 0.35`, `HOURS_DECAY_CONSTANT = 20` (raw gain
reaches ~63% of its ceiling around 20 hours — chosen so the brief's own "20
hours" example scenarios sit mid-curve, not at either extreme).

**Diminishing returns, twice over**: the exponential hours curve caps any
single allocation's raw gain, and `headroom_factor` further shrinks gains
as a component's score approaches 1.0. When a scenario has two allocations
mapped to the *same* component (e.g. two technical skills), they are
applied sequentially — the second allocation's `headroom_factor` is
computed against the *running* score after the first, so total gain from
two allocations to one component is sub-additive, never double-counted.
Locked in by `test_two_allocations_same_component_show_within_scenario_diminishing_returns`.

## Per-allocation confidence

```
evidence_confidence  = min(1, evidence_count / 3) * (0.4 + 0.4 * min(1, evidence_diversity / 2))
hours_penalty        = 0.6 + 0.4 / (1 + hours / 40)      # larger time commitments compound estimation uncertainty
confidence            = clamp(evidence_confidence * hours_penalty * (0.7 + 0.3 * role_importance), 0.05, 0.9)
uncertainty           = 1 - confidence
```

A component's confidence is the mean confidence across its own
allocation(s). Overall confidence is the mean of all changed components'
confidences, scaled by `coverage = (components with a score) / 6` — the
same coverage-discount pattern used by the Career Twin's own overall
confidence (see `CAREER_TWIN_SCORING.md`).

## Overall score

```
simulated_overall = mean(simulated score for touched components, current score for untouched-but-scored components)
current_overall   = mean(current score of components already scored, or null if no Career Twin snapshot exists yet)
overall_delta     = simulated_overall - current_overall   (null if current_overall is null)
```

## What the engine will not do

- Never calls a model to produce a number. `ExperimentExplainerAgent`
  receives only the already-computed `component_changes`/`overall_delta`
  and can only choose wording; its deterministic (no-API-key) fallback
  restates the same numbers in a fixed template, proving the fallback path
  can't fabricate content either.
- Never reports a result without the assumptions that produced it —
  `assumptions` always explains which fallback defaults were used (no JD on
  file, no history yet, unrecognized skill/activity type).
- Every result carries the fixed disclaimer: *"Personalized scenario
  estimate—not a guaranteed outcome or hiring prediction."*

## Tests

`backend/tests/test_simulation_engine.py` (10 tests): engine/version
constants, no-Twin-yet neutral-prior behavior, unresolved-skill safety,
more-hours-more-gain-with-diminishing-returns, job-description-requirement
raises gain, positive-historical-trend raises gain, mixed allocations
affect independent components, two-allocations-same-component
sub-additivity, and confidence/uncertainty complementarity.

`backend/tests/test_experiments_api.py` (6 tests): scenario creation with
disclaimer, empty-allocation rejection, mixed-allocation multi-component
coverage, three-way side-by-side comparison (the brief's own "20h SQL vs
20h DSA vs 20h communication" example), and cross-student authorization
isolation.
