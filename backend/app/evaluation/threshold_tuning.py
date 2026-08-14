"""Empirical threshold tuning: docs/05_CARE_ENGINE_SPEC.md documents the
0.80 / 0.55 / 0.50 routing thresholds as hypotheses "that must be tuned
through evaluation" -- this sweeps candidate values against the curated
routing case set (app/evaluation/cases.py) using the real `decide_route`
function (via its optional threshold-override parameters, see
app/care_engine/policy.py) and reports the empirical optimum, closing that
documented gap instead of leaving it as an unverified claim.
"""

from itertools import product

from sqlalchemy.orm import Session

from app.care_engine.policy import (
    HUMAN_REVIEW_CONFIDENCE_THRESHOLD,
    MULTI_AGENT_CONFIDENCE_THRESHOLD,
    SINGLE_AGENT_CONFIDENCE_THRESHOLD,
    decide_route,
)
from app.care_engine.schemas import RoutingFactors
from app.evaluation.cases import EVALUATION_CASES
from app.models.evaluation import EvaluationRun

THRESHOLD_TUNING_VERSION = "threshold-tuning-v1"

_SINGLE_AGENT_CANDIDATES = [0.70, 0.75, 0.80, 0.85, 0.90]
_MULTI_AGENT_CANDIDATES = [0.45, 0.50, 0.55, 0.60, 0.65]
_HUMAN_REVIEW_CANDIDATES = [0.40, 0.45, 0.50, 0.55]

_MIN_SAMPLE_FOR_NON_PRELIMINARY = 30


def _agreement_rate(single_agent: float, multi_agent: float, human_review: float) -> float:
    matches = 0
    for case in EVALUATION_CASES:
        factors = RoutingFactors(task_type=case["task_type"], **case["factors"])
        route = decide_route(factors, single_agent_threshold=single_agent, multi_agent_threshold=multi_agent, human_review_threshold=human_review)
        if route == case["expected_route"]:
            matches += 1
    return round(matches / len(EVALUATION_CASES), 4)


def run_threshold_tuning(db: Session) -> dict:
    default_agreement = _agreement_rate(
        SINGLE_AGENT_CONFIDENCE_THRESHOLD, MULTI_AGENT_CONFIDENCE_THRESHOLD, HUMAN_REVIEW_CONFIDENCE_THRESHOLD
    )

    results = []
    best = None
    for single_agent, multi_agent, human_review in product(_SINGLE_AGENT_CANDIDATES, _MULTI_AGENT_CANDIDATES, _HUMAN_REVIEW_CANDIDATES):
        if not (human_review <= multi_agent <= single_agent):
            # Only combinations preserving the documented ordering
            # (human_review <= multi_agent <= single_agent) are physically
            # meaningful routing policies -- sweeping the rest would just be
            # noise, not a real candidate policy.
            continue
        agreement = _agreement_rate(single_agent, multi_agent, human_review)
        row = {
            "single_agent_threshold": single_agent,
            "multi_agent_threshold": multi_agent,
            "human_review_threshold": human_review,
            "agreement_rate": agreement,
        }
        results.append(row)
        if best is None or agreement > best["agreement_rate"]:
            best = row

    run = EvaluationRun(
        name="Empirical threshold tuning sweep",
        dataset_name=THRESHOLD_TUNING_VERSION,
        notes=(
            f"Swept {len(results)} valid (single_agent, multi_agent, human_review) threshold combinations "
            f"against {len(EVALUATION_CASES)} curated routing cases via the real decide_route() function."
        ),
    )
    db.add(run)
    db.commit()

    return {
        "run_id": str(run.id),
        "case_count": len(EVALUATION_CASES),
        "combinations_swept": len(results),
        "current_defaults": {
            "single_agent_threshold": SINGLE_AGENT_CONFIDENCE_THRESHOLD,
            "multi_agent_threshold": MULTI_AGENT_CONFIDENCE_THRESHOLD,
            "human_review_threshold": HUMAN_REVIEW_CONFIDENCE_THRESHOLD,
            "agreement_rate": default_agreement,
        },
        "empirical_best": best,
        "matches_current_defaults": best is not None and (
            best["single_agent_threshold"] == SINGLE_AGENT_CONFIDENCE_THRESHOLD
            and best["multi_agent_threshold"] == MULTI_AGENT_CONFIDENCE_THRESHOLD
            and best["human_review_threshold"] == HUMAN_REVIEW_CONFIDENCE_THRESHOLD
        ),
        # The sweep reports the first-found combination tied for the top
        # agreement rate -- current_defaults_tied_for_best is what actually
        # matters for judging the documented thresholds: it's true whenever
        # no candidate beats them, even if a different combination is
        # reported as "best" due to tie-breaking order.
        "current_defaults_tied_for_best": best is not None and default_agreement >= best["agreement_rate"],
        "all_results": results,
        "preliminary": len(EVALUATION_CASES) < _MIN_SAMPLE_FOR_NON_PRELIMINARY,
        "methodology_note": (
            "Swept against the same 8-case curated rubric used by Experiment A (app/evaluation/cases.py), not a "
            "large human-labeled benchmark -- treat the empirical optimum as a direction, not a final answer; a "
            "larger labeled dataset is required before changing production thresholds."
        ),
    }
