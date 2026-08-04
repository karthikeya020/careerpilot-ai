import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.errors import NotFoundError
from app.evaluation.calibration import compute_calibration
from app.evaluation.graph_vs_vector import run_graph_vs_vector_evaluation
from app.evaluation.run import run_evaluation
from app.models.evaluation import EvaluationRun
from app.schemas.research import (
    CalibrationReportOut,
    EvaluationRunSummaryOut,
    GraphVsVectorExperimentOut,
    ReliabilityBinOut,
    RoutingExperimentOut,
)

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/experiments/routing", response_model=RoutingExperimentOut)
def run_routing_experiment(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> dict:
    return run_evaluation(db, write_report_file=False)


@router.post("/experiments/graph-vs-vector", response_model=GraphVsVectorExperimentOut)
def run_graph_vs_vector_experiment(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> dict:
    return run_graph_vs_vector_evaluation(db)


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
