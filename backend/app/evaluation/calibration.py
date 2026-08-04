"""Confidence calibration analysis over stored `EvaluationResult` rows:
reliability bins, Brier score, and Expected Calibration Error (ECE).
Computed entirely from real persisted evaluation outcomes -- never
fabricated -- and explicitly labeled `preliminary` below a minimum sample
size rather than presented with false confidence.
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import EvaluationResult

_MIN_SAMPLE_FOR_NON_PRELIMINARY = 30
_HIGH_CONFIDENCE_THRESHOLD = 0.8


@dataclass
class ReliabilityBin:
    bin_start: float
    bin_end: float
    count: int
    mean_confidence: float | None
    accuracy: float | None


@dataclass
class CalibrationReport:
    sample_size: int
    brier_score: float | None
    expected_calibration_error: float | None
    bins: list[ReliabilityBin] = field(default_factory=list)
    high_confidence_error_rate: float | None = None
    preliminary: bool = True


def compute_calibration(db: Session, run_id: uuid.UUID | None = None, num_bins: int = 5) -> CalibrationReport:
    stmt = select(EvaluationResult).where(EvaluationResult.accuracy_label.is_not(None))
    if run_id is not None:
        stmt = stmt.where(EvaluationResult.run_id == run_id)
    results = db.scalars(stmt).all()

    if not results:
        return CalibrationReport(sample_size=0, brier_score=None, expected_calibration_error=None)

    outcomes = [(float(r.confidence), 1.0 if r.accuracy_label == "match" else 0.0) for r in results]
    n = len(outcomes)
    brier = sum((c - y) ** 2 for c, y in outcomes) / n

    bin_width = 1.0 / num_bins
    bins: list[ReliabilityBin] = []
    ece = 0.0
    for i in range(num_bins):
        lo, hi = i * bin_width, (i + 1) * bin_width
        bucket = [(c, y) for c, y in outcomes if (lo <= c < hi) or (i == num_bins - 1 and c >= hi)]
        if not bucket:
            bins.append(ReliabilityBin(round(lo, 2), round(hi, 2), 0, None, None))
            continue
        mean_conf = sum(c for c, _ in bucket) / len(bucket)
        accuracy = sum(y for _, y in bucket) / len(bucket)
        ece += (len(bucket) / n) * abs(mean_conf - accuracy)
        bins.append(ReliabilityBin(round(lo, 2), round(hi, 2), len(bucket), round(mean_conf, 4), round(accuracy, 4)))

    high_conf = [(c, y) for c, y in outcomes if c >= _HIGH_CONFIDENCE_THRESHOLD]
    high_confidence_error_rate = round(1 - sum(y for _, y in high_conf) / len(high_conf), 4) if high_conf else None

    return CalibrationReport(
        sample_size=n,
        brier_score=round(brier, 4),
        expected_calibration_error=round(ece, 4),
        bins=bins,
        high_confidence_error_rate=high_confidence_error_rate,
        preliminary=n < _MIN_SAMPLE_FOR_NON_PRELIMINARY,
    )
