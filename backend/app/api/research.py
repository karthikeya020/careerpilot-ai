import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.errors import NotFoundError
from app.evaluation.ablations import run_full_ablation_suite
from app.evaluation.adversarial import run_adversarial_suite
from app.evaluation.calibration import compute_calibration
from app.evaluation.drift_canary import run_drift_canary
from app.evaluation.efficiency_frontier import run_efficiency_frontier_evaluation
from app.evaluation.fairness_probe import run_fairness_probe
from app.evaluation.fallback_fidelity import run_fallback_fidelity_check
from app.evaluation.graph_vs_vector import run_graph_vs_vector_evaluation
from app.evaluation.live_ablation import run_live_critic_toggle
from app.evaluation.report_generator import generate_research_report
from app.evaluation.run import run_evaluation
from app.evaluation.threshold_tuning import run_threshold_tuning
from app.models.evaluation import EvaluationRun
from app.schemas.research import (
    AblationSuiteOut,
    AdversarialSuiteOut,
    CalibrationReportOut,
    DriftCanaryOut,
    EfficiencyFrontierOut,
    EvaluationRunSummaryOut,
    FairnessProbeOut,
    FallbackFidelityOut,
    GraphVsVectorExperimentOut,
    LiveCriticToggleOut,
    LiveCriticToggleRequest,
    ReliabilityBinOut,
    ResearchReportOut,
    RoutingExperimentOut,
    ThresholdTuningOut,
)

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/experiments/routing", response_model=RoutingExperimentOut)
def run_routing_experiment(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> dict:
    return run_evaluation(db, write_report_file=False)


@router.post("/experiments/graph-vs-vector", response_model=GraphVsVectorExperimentOut)
def run_graph_vs_vector_experiment(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> dict:
    return run_graph_vs_vector_evaluation(db)


@router.post("/experiments/ablations", response_model=AblationSuiteOut)
def run_ablation_suite(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> dict:
    """Runs all six named ablation seams (CARE, graph retrieval, vector
    retrieval, Career Twin memory, reflection, consensus) and returns one
    consolidated report. See app/evaluation/ablations.py. The Career Twin
    memory ablation uses the most recently created student profile in the
    database (not necessarily the caller's -- this is a system-wide research
    harness, not a per-student report)."""
    return run_full_ablation_suite(db)


@router.get("/runs", response_model=list[EvaluationRunSummaryOut])
def list_runs(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list[EvaluationRunSummaryOut]:
    runs = db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(50)).all()
    return [
        EvaluationRunSummaryOut(
            id=run.id, name=run.name, dataset_name=run.dataset_name, notes=run.notes,
            created_at=run.created_at, result_count=len(run.results),
        )
        for run in runs
    ]


@router.get("/calibration", response_model=CalibrationReportOut)
def get_calibration(
    run_id: uuid.UUID | None = None, db: Session = Depends(get_db), _user=Depends(get_current_user)
) -> CalibrationReportOut:
    if run_id is not None and db.get(EvaluationRun, run_id) is None:
        raise NotFoundError("Evaluation run not found.")
    report = compute_calibration(db, run_id=run_id)
    return CalibrationReportOut(
        sample_size=report.sample_size,
        brier_score=report.brier_score,
        expected_calibration_error=report.expected_calibration_error,
        bins=[ReliabilityBinOut(**b.__dict__) for b in report.bins],
        high_confidence_error_rate=report.high_confidence_error_rate,
        preliminary=report.preliminary,
    )


@router.post("/experiments/efficiency-frontier", response_model=EfficiencyFrontierOut)
def run_efficiency_frontier(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> dict:
    """Real latency and LLM-call cost proxy vs accuracy for
    always-single-agent, always-multi-agent, and CARE-adaptive routing."""
    return run_efficiency_frontier_evaluation(db)


@router.post("/experiments/threshold-tuning", response_model=ThresholdTuningOut)
def run_threshold_tuning_sweep(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> dict:
    """Sweeps candidate CARE routing thresholds against the curated routing
    case set and reports the empirical optimum."""
    return run_threshold_tuning(db)


@router.post("/experiments/adversarial", response_model=AdversarialSuiteOut)
def run_adversarial_robustness_suite(_user=Depends(get_current_user)) -> dict:
    """Deliberately hostile inputs run through real production agents; pass
    criterion is that confidence stays low and nothing wrongly escalates."""
    return run_adversarial_suite()


@router.post("/experiments/fallback-fidelity", response_model=FallbackFidelityOut)
def run_fallback_fidelity(_user=Depends(get_current_user)) -> dict:
    """Compares the deterministic fallback provider's output against a live
    provider's on identical input; honestly reports "not measurable" when no
    live key is configured, rather than inventing a number."""
    return run_fallback_fidelity_check()


@router.post("/experiments/fairness-probe", response_model=FairnessProbeOut)
def run_fairness_probe_experiment(_user=Depends(get_current_user)) -> dict:
    """Measures scoring-function sensitivity to phrasing style across
    semantically-equivalent answer pairs -- never a bias-free claim, never an
    inference about any student."""
    return run_fairness_probe()


@router.post("/experiments/drift-canary", response_model=DriftCanaryOut)
def run_scoring_drift_canary(_user=Depends(get_current_user)) -> dict:
    """Re-runs a frozen, checked-in case set against the live agent code
    path and flags any confidence/score drift beyond tolerance."""
    return run_drift_canary()


@router.post("/experiments/live-critic-toggle", response_model=LiveCriticToggleOut)
def run_live_critic_toggle_demo(payload: LiveCriticToggleRequest, _user=Depends(get_current_user)) -> dict:
    """Interactive on-stage demo: type one answer, see the Critic pass's
    confidence effect appear in real time, side-by-side with critic-off."""
    return run_live_critic_toggle(
        transcript=payload.transcript, question_prompt=payload.question_prompt, expected_keywords=payload.expected_keywords
    )


@router.get("/report", response_model=ResearchReportOut)
def get_research_report(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> dict:
    """Assembles every Research Lab section into one exportable report --
    the same real, freshly-run modules each individual button calls, bundled
    into a single artifact rather than a working-app screenshot."""
    return generate_research_report(db)
