"""`python -m app.evaluation.run` -- compares three routing strategies over
the curated case set (docs/06_EVALUATION_PLAN.md Experiment A):

1. single_agent_fixed -- always uses one specialist, regardless of evidence.
2. multi_agent_fixed  -- always convenes a multi-agent council.
3. care_adaptive      -- CARE's real `decide_route` policy.

Results are persisted to `evaluation_runs`/`evaluation_results` (for Phase 3
dashboards) and written to a JSON file under `var/evaluation/` for quick
inspection without a DB connection.
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.care_engine.policy import decide_route
from app.care_engine.schemas import RoutingFactors
from app.core.config import get_settings
from app.evaluation.cases import EVALUATION_CASES
from app.models.evaluation import EvaluationResult, EvaluationRun

VARIANTS = ["single_agent_fixed", "multi_agent_fixed", "care_adaptive"]


def _route_for_variant(variant: str, factors: RoutingFactors) -> str:
    if variant == "single_agent_fixed":
        return "single_agent"
    if variant == "multi_agent_fixed":
        return "multi_agent"
    return decide_route(factors)


def run_evaluation(db: Session, dataset_name: str = "phase2-curated-v1", write_report_file: bool = True) -> dict:
    run = EvaluationRun(
        name="CARE routing comparison", dataset_name=dataset_name,
        notes="Experiment A: single-agent baseline vs fixed multi-agent vs CARE adaptive routing.",
    )
    db.add(run)
    db.flush()

    summary: dict[str, dict[str, int]] = {v: {"matches": 0, "total": 0} for v in VARIANTS}
    rows = []

    for case in EVALUATION_CASES:
        for variant in VARIANTS:
            factors = RoutingFactors(task_type=case["task_type"], **case["factors"])
            route_selected = _route_for_variant(variant, factors)
            matches_expected = route_selected == case["expected_route"]
            confidence = factors.agent_confidence
            if confidence is None:
                confidence = factors.retrieval_confidence if factors.retrieval_confidence is not None else 0.5

            summary[variant]["total"] += 1
            summary[variant]["matches"] += 1 if matches_expected else 0

            result = EvaluationResult(
                run_id=run.id,
                case_id=case["case_id"],
                route_variant=variant,
                route_selected=route_selected,
                agents_invoked=[],
                confidence=confidence,
                agreement=1.0 if matches_expected else 0.0,
                latency_ms=0.0,
                token_usage={},
                cost_usd=0.0,
                accuracy_label="match" if matches_expected else "mismatch",
                failure=False,
                retry_count=0,
                human_review=route_selected == "human_review",
            )
            db.add(result)
            rows.append(
                {
                    "case_id": case["case_id"],
                    "variant": variant,
                    "route_selected": route_selected,
                    "expected_route": case["expected_route"],
                    "matches_expected": matches_expected,
                    "confidence": confidence,
                }
            )

    db.commit()
    run_id = str(run.id)

    agreement_rate = {
        variant: round(summary[variant]["matches"] / summary[variant]["total"], 4) for variant in VARIANTS
    }

    report = {
        "run_id": run_id,
        "dataset_name": dataset_name,
        "case_count": len(EVALUATION_CASES),
        "agreement_rate_by_variant": agreement_rate,
        "rows": rows,
    }

    if write_report_file:
        output_dir = Path(get_settings().upload_dir).parent / "evaluation"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{run_id}.json"
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["output_path"] = str(output_path)
    return report


def main() -> None:
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        report = run_evaluation(db)
    finally:
        db.close()

    print(f"Evaluation run {report['run_id']} -- {report['case_count']} cases")
    for variant, rate in report["agreement_rate_by_variant"].items():
        print(f"  {variant}: {rate * 100:.0f}% agreement with rubric labels")
    print(f"Results written to {report['output_path']}")


if __name__ == "__main__":
    main()
