# Career Twin Scoring — Formula `twin-v2`

Implemented in `backend/app/career_twin/scoring.py`. Deterministic, no LLM
call, versioned via `formula_version` on every `CareerTwinSnapshot`.

## Inputs

The only input is the set of `SkillEvidence` rows stored for a student at the
moment of scoring. Evidence is written by:

- **Onboarding** — self-assessed skill ratings (`evidence_type=self_assessment`,
  weight `0.5`, confidence `0.4` — self-report is real signal but weaker than
  observed evidence).
- **Resume parsing** — skills detected in resume text (`evidence_type=resume`
  or `project` when the mention is inside the Projects section), weight/
  confidence set per match strength (see `RESUME_PARSING.md`).
- **Resume↔JD matching** — matched requirement skills
  (`evidence_type=job_description_match`), feeding role alignment.
- **Technical assessment** (Phase 2) — each answered question in the
  adaptive SQL/Python assessment engine
  (`backend/app/services/assessment_service.py`) becomes one
  `evidence_type=technical_assessment` row, linked to both a `Skill` and the
  specific `Concept` tested (`SkillEvidence.concept_id`, new in Phase 2) —
  this concept link is what makes GraphRAG root-cause analysis possible.

Interviews still don't exist (Phase 3 item), so no evidence type feeds from
them yet.

## Six readiness components

| Component | Evidence considered |
|---|---|
| `resume_readiness` | All evidence sourced from the resume (`resume` + `project` types) |
| `technical_readiness` | Evidence for skills in category `technical` or `tools`, any source (including assessment evidence for a technical skill) |
| `communication_readiness` | Evidence for skills in category `communication` or `soft_skill` |
| `assessment_readiness` | Evidence tagged `technical_assessment` (Phase 2 — was always `insufficient_evidence` in Phase 1, before the assessment engine existed) |
| `portfolio_readiness` | Evidence tagged `project` (Projects section of the resume) |
| `role_alignment_readiness` | Evidence tagged `job_description_match` |

A single assessment answer can count toward both `assessment_readiness`
(because it's assessment-sourced) and `technical_readiness` (because the
skill is technical) — components are different lenses on the same evidence,
not a mutually-exclusive partition. This mirrors how resume evidence already
counted toward both `resume_readiness` and `technical_readiness` in Phase 1.

## Per-component formula

Given evidence items `e_1..e_n` for a component, each with
`normalized_score ∈ [0,1]`, `weight ∈ [0,1]`, `confidence ∈ [0,1]`,
`source_object_type` (e.g. `resume`, `interview_answer`,
`question_response`):

```
raw_weighted_score = Σ(normalized_score_i * weight_i) / Σ(weight_i)
raw_confidence      = Σ(confidence_i * weight_i) / Σ(weight_i)
volume_factor       = min(1, evidence_count / SATURATION[component])
```

`SATURATION` (evidence count at which volume_factor reaches 1.0) is 3 for
resume/communication/assessment/role-alignment, 4 for technical, 2 for
portfolio. With zero evidence, the component is stored with
`status=insufficient_evidence`, `score=null`, `confidence=null`, and a plain
-language explanation — never a fabricated number.

## Small-sample safeguard (`twin-v2`)

A single session of evidence — for example, two interview answers, both
scoring 90%+ — must never be presented as a confidently established skill
level. Formula `twin-v1` already discounted confidence by evidence volume,
but nothing stopped the *score itself* from reporting the raw 90%+ value, and
nothing distinguished "five answers in one interview" from "five
observations across independent sources." `twin-v2` adds three deterministic
levers, all versioned in this same formula:

**1. Evidence-diversity weighting.** `evidence_diversity` is the count of
distinct `source_object_type` values behind a component's evidence.

```
distinct_sources  = |{source_object_type_i}|
diversity_factor  = min(1, distinct_sources / MIN_SOURCE_DIVERSITY_TARGET)   # target = 2
```

Five items from one interview session (`distinct_sources = 1`) score the
same `diversity_factor` as one item from that session — volume alone cannot
substitute for independent corroboration.

**2. Prior-weighted (shrinkage) scoring.** The *stored* `score` — not just
confidence — is pulled toward a neutral 0.5 prior in proportion to how
little the evidence can be trusted:

```
trust_factor = volume_factor * diversity_factor
score        = raw_weighted_score * trust_factor + NEUTRAL_SCORE_PRIOR * (1 - trust_factor)   # prior = 0.5
```

A single perfect 0.95 answer (`volume_factor≈0.25` for a technical
component saturating at 4, `diversity_factor=0.5` for one source) reports
around **0.55**, not 0.95. This is a standard Bayesian-shrinkage /
empirical-Bayes correction: with little evidence, regress toward a neutral
prior rather than trusting the sample at face value.

**3. Hard confidence cap + explicit low-sample flag.**

```
confidence = raw_confidence * volume_factor * diversity_factor
if disagreement > HIGH_DISAGREEMENT_THRESHOLD (0.25):     # population stdev of normalized_score
    confidence *= (1 - disagreement)                       # conflicting evidence discount
is_low_sample = evidence_count < MIN_EVIDENCE_FOR_STABLE_CONFIDENCE (3)
                or distinct_sources < MIN_SOURCE_DIVERSITY_TARGET (2)
if is_low_sample:
    confidence = min(confidence, LOW_SAMPLE_CONFIDENCE_CAP)   # 0.50
```

When `is_low_sample` is true, `ReadinessComponent.is_low_sample=True` and
`explanation` (and the API's `low_sample_notice` field) carries the exact
text:

> "Strong performance in this session, but more evidence is required to
> establish long-term proficiency."

`evidence_diversity` and `is_low_sample` are stored columns on
`ReadinessComponent` (migration `7ba5f89c3126`), not derived-on-read, so the
Trust Center and audit trail can show exactly why a score was shrunk.

**What "clears" low-sample status**: evidence at or above the volume
threshold (3+ items) *and* spread across 2+ distinct source types — e.g. an
interview answer, a resume mention, and an assessment question response
about the same skill. That evidence combination reaches `trust_factor≈1`
(score reported near its raw value) and is allowed to exceed the 0.50
confidence cap.

Tests: `backend/tests/test_career_twin_small_sample_safeguard.py` — one
strong answer (shrunk, low-sample), several strong answers from one source
(still low-sample despite volume), conflicting evidence (confidence further
discounted, notice present), repeated evidence from one source (diversity
stays capped), and evidence from multiple independent sources (clears
low-sample, score/confidence approach raw values).

## Overall score

```
scored = components where status == "scored"
overall_score      = mean(score of scored components)
coverage           = len(scored) / 6
overall_confidence = mean(confidence of scored components) * coverage
```

The `coverage` multiplier means overall confidence drops as components remain
unscored (e.g., no resume yet, no JD yet), even if the components that *are*
scored are individually confident — reflecting that the Twin only knows part
of the picture.

## Versioning and audit trail

Every `recompute_twin()` call:

1. Reads the previous snapshot for the student (if any) and computes
   `score_delta` and a plain-language `change_summary`.
2. Writes a new `CareerTwinSnapshot` (`version = previous + 1`) plus one
   `ReadinessComponent` row per component, each carrying its own
   `evidence_ids` list.
3. Writes one `DecisionTrace` (`task_type=career_twin_update`,
   `route=deterministic_rule`, `model_versions={"scoring_formula": "twin-v2"}`)
   referencing the same evidence IDs.
4. Writes one `AuditEvent` (`event_type=career_twin_updated`).

All in the same DB transaction, so a snapshot is never written without its
trace and audit record.

## Trigger points

`recompute_twin` is called after: onboarding completion, resume parsing
finishing, job-description matching finishing, and (Phase 2) assessment
attempt completion. Each call passes a human-readable `reason` string that
becomes part of `change_summary`.

## Trend and uncertainty (Phase 2, derived — not stored)

`build_career_twin_snapshot_out()` (`app/career_twin/scoring.py`) attaches
two extra fields to each component on read, computed from already-stored
snapshot data rather than new columns:

- `trend` = this component's `score` minus the same component's `score` in
  the previous snapshot (`null` if there is no previous snapshot or the
  component wasn't scored then).
- `uncertainty` = `1 - confidence` (`null` if the component has no
  confidence, i.e. `insufficient_evidence`).

Neither is a new evidence source — both are pure functions of data that was
already written by `recompute_twin`.

## Root-cause-aware mission generation (Phase 2)

When `generate_mission_for_snapshot` (`app/services/mission_service.py`)
runs, it checks whether the most recent `SkillEvidence` batch is a fresh
incorrect assessment answer (or falls back to the priority component's
weakest evidence). If so, it calls
`app/services/autonomous_loop_service.py::build_root_cause_mission_plan`,
which runs a real CARE-routed root-cause analysis (GraphRAG, then a
career-coach synthesis — see `PHASE_2_COMPLETION_REPORT.md` §4-5) and
produces a mission with a concrete `root_cause` path, `tasks`,
`resource_ids`, and an `expected_impact_estimate` — always labeled an
estimate, never a guarantee. A generic priority-component template remains
the fallback when there's no assessment evidence to explain.
