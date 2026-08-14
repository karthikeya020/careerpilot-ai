"""Auto-generated research report: assembles calibration, ablations,
efficiency frontier, threshold tuning, adversarial robustness, fallback
fidelity, fairness probe, and drift canary results into one structured,
exportable artifact -- reframing the project as producing a research
artifact, not just a working app. Every section is a real, freshly-run (or
freshly-queried, for calibration) result computed by the same modules the
Research Lab's individual buttons call; nothing here is invented or
recomputed with a second parallel formula.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.evaluation.ablations import run_full_ablation_suite
from app.evaluation.adversarial import run_adversarial_suite
from app.evaluation.calibration import compute_calibration
from app.evaluation.drift_canary import run_drift_canary
from app.evaluation.efficiency_frontier import run_efficiency_frontier_evaluation
from app.evaluation.fairness_probe import run_fairness_probe
from app.evaluation.fallback_fidelity import run_fallback_fidelity_check
from app.evaluation.threshold_tuning import run_threshold_tuning

RESEARCH_REPORT_VERSION = "research-report-v1"


def generate_research_report(db: Session) -> dict:
    calibration = compute_calibration(db)
    ablations = run_full_ablation_suite(db)
    efficiency = run_efficiency_frontier_evaluation(db)
    thresholds = run_threshold_tuning(db)
    adversarial = run_adversarial_suite()
    fidelity = run_fallback_fidelity_check()
    fairness = run_fairness_probe()
    drift = run_drift_canary()

    return {
        "report_version": RESEARCH_REPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "calibration": {
            "sample_size": calibration.sample_size,
            "brier_score": calibration.brier_score,
            "expected_calibration_error": calibration.expected_calibration_error,
            "high_confidence_error_rate": calibration.high_confidence_error_rate,
            "preliminary": calibration.preliminary,
            "bins": [b.__dict__ for b in calibration.bins],
        },
        "ablations": ablations,
        "efficiency_frontier": efficiency,
        "threshold_tuning": thresholds,
        "adversarial_suite": adversarial,
        "fallback_fidelity": fidelity,
        "fairness_probe": fairness,
        "drift_canary": drift,
    }
