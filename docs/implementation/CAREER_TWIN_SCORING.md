# Career Twin Scoring — Formula `twin-v1`

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
`normalized_score ∈ [0,1]`, `weight ∈ [0,1]`, `confidence ∈ [0,1]`:

```
weighted_score = Σ(normalized_score_i * weight_i) / Σ(weight_i)
raw_confidence = Σ(confidence_i * weight_i) / Σ(weight_i)
volume_factor  = min(1, evidence_count / SATURATION[component])
final_confidence = raw_confidence * volume_factor
```

`SATURATION` (evidence count at which volume_factor reaches 1.0) is 3 for
resume/communication/assessment/role-alignment, 4 for technical, 2 for
portfolio — chosen so no component reports high confidence off a single data
point. With zero evidence, the component is stored with
`status=insufficient_evidence`, `score=null`, `confidence=null`, and a plain
-language explanation — never a fabricated number.

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
   `route=deterministic_rule`, `model_versions={"scoring_formula": "twin-v1"}`)
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
