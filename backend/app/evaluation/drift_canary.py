"""Scoring-drift canary: a frozen, checked-in evaluation set
(fixtures/canary_baseline.json) is re-run against the live TechnicalAgent
code path whenever this check runs, and the result is diffed against the
baseline recorded at freeze time. Any case whose confidence/correctness/
depth score drifts beyond tolerance is flagged -- a real production concern
(silent scoring drift after a prompt or model change) that most student
projects never consider, let alone test for.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from app.agents.technical_agent import TechnicalAgent, TechnicalInterviewInput

DRIFT_CANARY_VERSION = "drift-canary-v1"
_DRIFT_TOLERANCE = 0.05
_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "canary_baseline.json"


@dataclass
class CanaryCaseResult:
    case_id: str
    baseline_confidence: float
    current_confidence: float
    confidence_drift: float
    baseline_correctness_score: float
    current_correctness_score: float
    correctness_drift: float
    baseline_depth_score: float
    current_depth_score: float
    depth_drift: float
    drifted: bool


def run_drift_canary() -> dict:
    fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = []
    any_drifted = False

    for case in fixture["cases"]:
        output, _latency = TechnicalAgent().safe_run(
            TechnicalInterviewInput(
                question_prompt=case["question_prompt"], transcript=case["transcript"], expected_keywords=case["expected_keywords"]
            )
        )
        confidence_drift = round(output.confidence - case["baseline_confidence"], 4)
        correctness_drift = round(output.correctness_score - case["baseline_correctness_score"], 4)
        depth_drift = round(output.depth_score - case["baseline_depth_score"], 4)
        drifted = max(abs(confidence_drift), abs(correctness_drift), abs(depth_drift)) > _DRIFT_TOLERANCE
        any_drifted = any_drifted or drifted

        cases.append(
            CanaryCaseResult(
                case_id=case["case_id"],
                baseline_confidence=case["baseline_confidence"],
                current_confidence=output.confidence,
                confidence_drift=confidence_drift,
                baseline_correctness_score=case["baseline_correctness_score"],
                current_correctness_score=output.correctness_score,
                correctness_drift=correctness_drift,
                baseline_depth_score=case["baseline_depth_score"],
                current_depth_score=output.depth_score,
                depth_drift=depth_drift,
                drifted=drifted,
            ).__dict__
        )

    return {
        "engine_version": DRIFT_CANARY_VERSION,
        "baseline_frozen_at": fixture["frozen_at"],
        "baseline_engine": fixture["engine"],
        "tolerance": _DRIFT_TOLERANCE,
        "case_count": len(cases),
        "any_drifted": any_drifted,
        "cases": cases,
        "methodology_note": (
            "Re-runs the same frozen case set through the live TechnicalAgent code path on every call and diffs "
            "against outputs recorded once at freeze time -- re-freeze the fixture deliberately (never silently) "
            "whenever a prompt or model version change is intentional."
        ),
    }
